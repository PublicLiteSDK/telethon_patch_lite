import asyncio
import contextlib
import datetime
import os
import typing
from urllib.parse import urlparse, parse_qs

from telethon.errors import HashInvalidError, SessionPasswordNeededError, YouBlockedUserError, InviteRequestSentError
from telethon.tl.functions.account import GetAuthorizationsRequest, ResetAuthorizationRequest
from telethon.tl.functions.auth import AcceptLoginTokenRequest, SendCodeRequest, ImportWebTokenAuthorizationRequest
from telethon.tl.functions.channels import JoinChannelRequest, InviteToChannelRequest
from telethon.tl.functions.contacts import UnblockRequest
from telethon.tl.functions.help import GetPremiumPromoRequest
from telethon.tl.functions.messages import AcceptUrlAuthRequest, CheckChatInviteRequest, ImportChatInviteRequest
from telethon.tl.functions.payments import GetStarsStatusRequest

from telethon_patch.models.tgdc import TGDC

from telethon_patch.models.init_context import InitContext

from telethon_patch import helpers
from telethon.sessions import SQLiteSession, StringSession
from telethon.tl.types import User, Authorization, CodeSettings, MessageEntityTextUrl, InputPeerSelf, ChatInviteAlready, \
    TypeChat, ChatInvite, InputPeerUser
from telethon.client.telegrambaseclient import TelegramBaseClient
from telethon import client
import dateutil.parser

if typing.TYPE_CHECKING:
    from telethon_patch import TelegramClient


class ClientMethods:
    me: typing.Optional[User] = None
    twofa: typing.Optional[str] = None

    async def connect(
            self: "TelegramClient",
            retries=3,
            timeout=30,
            ignore_errors: bool = False,
            check_auth: bool = False
    ) -> bool:
        async def try_connect_once() -> bool:
            try:
                await asyncio.wait_for(client.TelegramBaseClient.connect(self), timeout=timeout)
                await self.get_me()

                if check_auth and not await self.is_user_authorized():
                    await self.send_message("me", "me")  # для отладки?

                return True

            except (asyncio.TimeoutError, asyncio.CancelledError):
                return False

            except Exception as exc:
                if self.is_connected():
                    await self.disconnect()

                if ignore_errors or (isinstance(exc, ConnectionError) and retries > 0):
                    return False

                raise

        while retries > 0:
            if await try_connect_once():
                return True

            retries -= 1

        return False

    async def disconnect(self: "TelegramClient"):
        with contextlib.suppress(Exception):
            await client.TelegramBaseClient.disconnect(self)

    async def get_me(self: "TelegramClient") -> User:
        self.me = await client.UserMethods.get_me(self)
        return self.me

    async def check_spambot(self: "TelegramClient", delete_dialog: bool = True) -> datetime.datetime:
        message = None
        async with self.conversation("@spambot") as conv:
            for _ in range(2):
                try:
                    await conv.send_message("/start")
                    message = await conv.get_response()
                    break

                except YouBlockedUserError:
                    await self(UnblockRequest(id="@spambot"))

        if delete_dialog:
            with contextlib.suppress(Exception):
                await self.delete_dialog("@spambot")

        if message is None:
            return datetime.datetime.now(datetime.UTC) + datetime.timedelta(days=7)

        have_url = any([isinstance(_, MessageEntityTextUrl) for _ in message.entities or []])
        if message.reply_markup and len(message.reply_markup.rows) == 2 and have_url is False:
            return None

        date = helpers.extract_date_from_text()
        if date is None:
            return datetime.datetime.now(datetime.UTC) + datetime.timedelta(days=30 * 6)

        if datetime.datetime.now(datetime.UTC) > date:
            return None

        return date

    async def check_twofa(self: "TelegramClient", value: str) -> typing.Optional[str]:
        with contextlib.suppress(Exception):
            value = (value or "").strip(" ")
            if await self.edit_2fa(current_password=value):
                self.twofa = value
                return self.twofa

    async def get_premium_expired(self: "TelegramClient") -> typing.Optional[datetime.datetime]:
        if self.me.premium is True:
            promo = await self(GetPremiumPromoRequest())
            return helpers.extract_date_from_text_by_re(promo.status_text)

    async def get_stars_balance(self: "TelegramClient") -> int:
        stars = await self(GetStarsStatusRequest(peer=InputPeerSelf()))
        return stars.balance.amount

    async def get_authorizations(self: "TelegramClient") -> list[Authorization]:
        return (await self(GetAuthorizationsRequest())).authorizations

    async def get_session_date_created(self: "TelegramClient") -> datetime.datetime:
        for auth in (await self.get_authorizations()):
            if auth.current is True:
                return auth.date_created

    async def reset_authorizations(self: "TelegramClient", skip_auth_dates: list[datetime.datetime] = None) -> int:
        reset_count = 0
        skip_times = {d.time() for d in skip_auth_dates} if skip_auth_dates else set()

        for auth in (await self.get_authorizations()):
            if auth.current or auth.date_created.time() in skip_times:
                continue

            try:
                await self(ResetAuthorizationRequest(auth.hash))
                reset_count += 1

            except HashInvalidError:
                continue

        return reset_count

    async def subscribe(
            self: "TelegramClient",
            link: str,
            invite_requests_enabled: bool = True,
            invite_requests_timeout: int = 10,
    ) -> typing.Union[TypeChat, bool]:
        if not ('joinchat' in link or '+' in link):
            entity = await self.get_entity(link)
            if entity.left is True:
                entity = (await self(JoinChannelRequest(link))).chats[0]

            return entity

        link = link.split('+' if '+' in link else '/')[-1]
        for retry in range(2):
            try:
                invite_type = (await self(CheckChatInviteRequest(link)))
                if isinstance(invite_type, ChatInviteAlready):
                    return invite_type.chat

                if any(
                        retry == 1,
                        (
                                isinstance(invite_type, ChatInvite)
                                and invite_requests_enabled is False
                        )
                ):
                    return False

                return (await self(ImportChatInviteRequest(link))).chats[0]

            except InviteRequestSentError:
                await asyncio.sleep(invite_requests_timeout)
                continue

            except:
                break

        return False

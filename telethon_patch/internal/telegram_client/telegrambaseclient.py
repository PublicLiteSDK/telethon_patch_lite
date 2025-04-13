import abc
import asyncio
import asyncio
import logging
import typing
from abc import ABC

from telethon import helpers
from telethon._updates import EntityType, Entity, SessionState, ChannelState
from telethon.network import Connection, ConnectionTcpFull
from telethon.sessions import Session, MemorySession, SQLiteSession, StringSession
from telethon.tl import functions
from telethon.tl.alltlobjects import LAYER

from telethon.client.telegrambaseclient import TelegramBaseClient
from telethon.tl.types import User

from telethon_patch.models import InitContext
from telethon_patch.models.json_context import JsonContext
from telethon_patch.models.session_context import SessionContext
from telethon_patch.models.tgdc import TGDC

from telethon import TelegramClient as TelethonClientOriginal

if typing.TYPE_CHECKING:
    from telethon_patch import TelegramClient

from telethon import TelegramClient as TelethonClientOriginal


class TelegramBaseV2Client(TelethonClientOriginal):
    session: typing.Union[MemorySession, SQLiteSession, StringSession]
    _init_request: functions.InitConnectionRequest

    init_context: InitContext = InitContext
    json_context: JsonContext = JsonContext
    session_context: SessionContext

    def __init__(
            self: typing.Union['TelegramClient'],
            session: 'typing.Union[str, Session]',
            init_context: InitContext = None,
            json_context: JsonContext = None,
            proxy: typing.Union[tuple, dict] = None,
    ):

        if init_context is None or isinstance(init_context, InitContext) is False:
            if json_context is None or isinstance(json_context, JsonContext) is False:
                raise ValueError("init_context or json_context must be provided")

            init_context = InitContext.load_from_json_context(json_context.content)

        if isinstance(session, str):
            session = SQLiteSession(str(session))

        self.session_context = SessionContext.init(session)

        super().__init__(
            session=self.session_context.session,
            api_id=init_context.app_id,
            api_hash=init_context.app_hash,
            device_model=init_context.device_model,
            app_version=init_context.app_version,
            system_version=init_context.system_version,
            lang_code=init_context.lang_code,
            system_lang_code=init_context.system_lang_code,
            proxy=proxy
        )

        if self.session._server_address is not None and self.session._server_address[0] == "0":
            self.session._server_address = TGDC.get(self.session._dc_id, self.session._server_address)

        self.init_context = init_context
        self.json_context = json_context

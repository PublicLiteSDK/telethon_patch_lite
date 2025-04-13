import abc
import asyncio
import asyncio
import contextlib
import logging
import typing

from telethon import helpers
from telethon._updates import EntityType, Entity, SessionState, ChannelState
from telethon.client import TelegramBaseClient as TelethonBaseClientOriginal
from telethon.network import Connection, ConnectionTcpFull
from telethon.sessions import Session
from telethon.tl import functions
from telethon.tl.alltlobjects import LAYER

if typing.TYPE_CHECKING:
    from telethon_patch import TelegramClient


class TelegramBaseClient(TelethonBaseClientOriginal):

    async def connect(self: 'TelegramClient') -> None:
        if self.session is None:
            raise ValueError('TelegramClient instance cannot be reused after logging out')

        if self._loop is None:
            self._loop = helpers.get_running_loop()
        elif self._loop != helpers.get_running_loop():
            raise RuntimeError('The asyncio event loop must not change after connection (see the FAQ for details)')

        if not await self._sender.connect(self._connection(
                self.session.server_address,
                self.session.port,
                self.session.dc_id,
                loggers=self._log,
                proxy=self._proxy,
                local_addr=self._local_addr
        )):
            # We don't want to init or modify anything if we were already connected
            return

        self.session.auth_key = self._sender.auth_key
        self.session.save()

        try:
            # See comment when saving entities to understand this hack
            self_id = self.session.get_input_entity(0).access_hash
            self_user = self.session.get_input_entity(self_id)
            self._mb_entity_cache.set_self_user(self_id, None, self_user.access_hash)
        except ValueError:
            pass

        if self._catch_up:
            ss = SessionState(0, 0, False, 0, 0, 0, 0, None)
            cs = []

            for entity_id, state in self.session.get_update_states():
                if entity_id == 0:
                    # TODO current session doesn't store self-user info but adding that is breaking on downstream session impls
                    ss = SessionState(0, 0, False, state.pts, state.qts, int(state.date.timestamp()), state.seq, None)
                else:
                    cs.append(ChannelState(entity_id, state.pts))

            self._message_box.load(ss, cs)
            for state in cs:
                try:
                    entity = self.session.get_input_entity(state.channel_id)
                except ValueError:
                    self._log[__name__].warning(
                        'No access_hash in cache for channel %s, will not catch up', state.channel_id)
                else:
                    self._mb_entity_cache.put(Entity(EntityType.CHANNEL, entity.channel_id, entity.access_hash))

        self._init_request.query = functions.help.GetConfigRequest()

        req = self._init_request
        if self._no_updates:
            req = functions.InvokeWithoutUpdatesRequest(req)

        response = await self._sender.send(functions.InvokeWithLayerRequest(LAYER, req))

        if isinstance(response, Exception):
            raise response

        if self._message_box.is_empty():
            me = await self.get_me()
            if me:
                await self._on_login(me)  # also calls GetState to initialize the MessageBox

        self._updates_handle = self.loop.create_task(self._update_loop())
        self._keepalive_handle = self.loop.create_task(self._keepalive_loop())

import asyncio
import os
import random
import time
import traceback
from typing import Optional

from simple_singleton import _SingletonMeta
from telethon_patch import TelegramClient, JsonContext, logger
from telethon_patch.lib import helpers


class AccountsStorage(metaclass=_SingletonMeta):
    __started__: bool = False

    _hold_until_at: dict[str, int]
    _clients: dict[TelegramClient, str]
    _semaphore: asyncio.Semaphore

    def __init__(self, input_dir_path: str, uncorrect_format_dir_path: Optional[str] = None):
        self.input_dir_path = input_dir_path
        self.uncorrect_format_dir_path = uncorrect_format_dir_path
        self._hold_until_at = dict()
        self._clients = dict()
        self._semaphore = asyncio.Semaphore()

    def set_hold(self, session: TelegramClient, add: int = 60) -> None:
        if (key := self._clients.get(session, None)) is None:
            return

        self._hold_until_at[key] = time.time() + add

    async def take(self) -> Optional[TelegramClient]:
        async with self._semaphore:
            _copy = list(self._clients.items()).copy()
            random.shuffle(_copy)
            for client, filename in _copy:
                hold_until_at = self._hold_until_at.get(filename)
                if hold_until_at is not None and time.time() < hold_until_at:
                    continue

                self.set_hold(client)
                return client

    async def _load(self):
        accounts = helpers.find_session_files(self.input_dir_path)
        for filename, data in accounts.items():
            if filename not in self._clients:
                try:
                    client = TelegramClient(
                        session=data["session_file"],
                        json_context=await JsonContext.load_json_file(data["json_file"])
                    )
                    self._clients[client] = filename

                except Exception as exc:
                    logger.debug(
                        "Error while initializing client {} ({}: {})".format(filename, exc.__class__.__name__, exc)
                    )
                    if self.uncorrect_format_dir_path:
                        os.makedirs(self.uncorrect_format_dir_path, exist_ok=True)
                        for file in (data["session_file"], data["json_file"]):
                            if os.path.exists(file):
                                os.rename(
                                    file,
                                    os.path.join(self.uncorrect_format_dir_path, filename + os.path.splitext(file)[1])
                                )

    async def _loader(self, interval: int = 60):
        async with self._semaphore:
            if self.__started__ is True:
                return

            self.__started__ = True

        while True:
            try:
                await self._load()

            except Exception as exc:
                logger.debug("Error while loading accounts ({}: {})", exc.__class__.__name__, str(exc))
                traceback.print_exc()

            await asyncio.sleep(interval)

    async def run_loader(self):
        asyncio.create_task(self._loader())

import asyncio
import os
import random
import time
import traceback
from typing import Union, Literal

import python_socks
from aiofile import async_open
from simple_singleton import Singleton
from telethon_patch import helpers, logger
from telethon_patch.errors import ProxyError

PROXY_TYPES = dict(
    http=python_socks.ProxyType.HTTP,
    socks=python_socks.ProxyType.SOCKS5
)


class Proxy:
    def __init__(
            self, line: str, proxy_type: Literal['http', 'socks']
    ) -> None:
        self.__raw = line

        item_pieces = line.split(':')
        self.__host = item_pieces[0]
        self.__port = item_pieces[1]
        self.__username = item_pieces[2] if len(item_pieces) > 2 else None
        self.__password = item_pieces[3] if len(item_pieces) > 3 else None
        self.__login_auth = True if (self.__username and self.__password) else False

        if not str(self.__port).isdigit():
            raise ProxyError('The host or port is not correct')

        if isinstance(proxy_type, str) and proxy_type.lower() in PROXY_TYPES:
            self.__proxy_type = PROXY_TYPES.get(proxy_type.lower(), None)

        elif isinstance(proxy_type, python_socks.ProxyType):
            self.__proxy_type = proxy_type

        else:
            raise ProxyError('The proxies.txt type is not correct')

        if proxy_type not in [python_socks.ProxyType.SOCKS5, python_socks.ProxyType.HTTP]:
            self.__proxy_type = proxy_type

        else:
            if proxy_type.lower() not in ['http', 'socks']:
                raise ProxyError('The proxies.txt type is not correct')

            self.__proxy_type = python_socks.ProxyType.SOCKS5 if proxy_type == 'socks' else python_socks.ProxyType.HTTP

    @property
    def host(self) -> str:
        return self.__host

    @property
    def port(self) -> int:
        return self.__port

    @property
    def username(self) -> str:
        return self.__username

    @property
    def password(self) -> str:
        return self.__password

    @property
    def login_auth(self) -> str:
        return self.__login_auth

    @property
    def proxy_type(self) -> str:
        return self.__proxy_type

    @property
    def raw(self) -> str:
        return self.__raw

    @property
    def format(self) -> list:
        return (
            self.proxy_type,
            self.host,
            self.port,
            *([self.login_auth, self.username, self.password] if self.login_auth else [])
        )


class ProxyStorage(metaclass=Singleton):
    _ignores: dict[str, list[int]] = {}
    _proxies: dict[str, Proxy] = {}
    _last_proxy_index = 0

    def ignore(self, proxy: str) -> None:
        self._ignores.setdefault(proxy, []).append(time.time())

    def add(self, proxies: Union[str, list[str]], proxy_type: Literal['http', 'socks'] = 'http') -> None:
        if isinstance(proxies, list) is False:
            proxies = [proxies]

        for item in proxies:
            try:
                if item not in self._proxies:
                    proxy_item = Proxy(item, proxy_type)
                    self._proxies[item] = proxy_item

            except:
                logger.error(f'The proxy {item} is not correct')
                traceback.print_exc()

    @property
    def proxies(self) -> list:
        return self._proxies

    def get_avaliable_proxies(self) -> list:
        proxies = []

        for proxy in self._proxies.values():
            ignores = self._ignores.get(proxy.raw, [])
            ignores_count = 0
            for ignore in ignores.copy():
                if time.time() - ignore > 60:
                    ignores.remove(ignore)
                    continue

                ignores_count += 1

            if ignores_count > 3:
                continue

            proxies.append(proxy)

        return proxies

    def get_proxy(self, _random: bool = True, _index: int = None, no_proxy_error: bool = False) -> Proxy:
        try:
            assert _index is None or isinstance(_index, int)
            assert _random is None or isinstance(_random, bool)
            assert _random is not None or _index is not None

        except AssertionError:
            raise ProxyError('The index or random is not correct')

        if _index is None:
            return self.proxies[_index]

        proxies = self.get_avaliable_proxies()
        if not proxies:
            if no_proxy_error is True:
                raise ProxyError('No proxies found')

            return None

        proxy = random.choice(proxies)
        return proxy

    def get_next_proxy(self):
        self._last_proxy_index = 1 if len(self.proxies) <= self._last_proxy_index else self._last_proxy_index + 1
        return self.get_proxy(_index=self._last_proxy_index - 1, _random=False)

    def sync_file_load(self, filename: str) -> None:
        with open(filename, mode='r', encoding='utf-8') as file:
            content = file.read()
            proxies = [line for _ in content.split("\n") if (line := _.strip())]

        self.add(proxies)

    async def file_load(self, filename: str) -> None:
        await helpers.run_sync(self.sync_file_load, filename)

    async def run_fetcher(self, fetch_task: callable, interval: int = 60) -> None:
        if not isinstance(fetch_task, callable):
            raise ProxyError('The load_task is not correct')

        async def wrap_fetch_task():
            while True:
                try:
                    await fetch_task(self)

                except Exception as exc:
                    logger.error("Error while loading proxies ({}: {})", exc.__class__.__name__, exc)

                await asyncio.sleep(interval)

        asyncio.create_task(wrap_fetch_task())

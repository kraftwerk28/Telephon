from typing import (Callable, List, Any, Union, AnyStr, Tuple,
                    Awaitable, Optional, Pattern, Dict)
from telethon import events, TelegramClient, tl
from dataclasses import dataclass
from aiohttp import ClientSession
from asyncio import AbstractEventLoop
import logging as log

from .utils import *


class TelephonBase:
    def __init__(self, init_config: InitConfig):
        client = TelegramClient(init_config.session_path,
                                init_config.api_id,
                                init_config.api_hash)

        self.client: TelegramClient = client
        self.http_client: ClientSession = ClientSession(loop=client.loop)

        log.basicConfig(format='[%(asctime)s] %(message)s',
                        datefmt='%d.%m.%Y %H:%M:%S',
                        level=log.INFO)

    async def _run_client(self):
        await self.client.start()
        log.info('Client started.')
        await self.client.run_until_disconnected()

    def start(self, loop: Optional[AbstractEventLoop] = None):
        loop = self.client.loop
        try:
            loop.run_until_complete(self._run_client())
        except KeyboardInterrupt:
            loop.run_until_complete(self.shutdown())
        finally:
            loop.close()
            log.info('Client loop closed.')
        return 0

    async def shutdown(self):
        self.client.remove_event_handler(self._on_message)
        self.client.remove_event_handler(self._on_delete)
        log.info('Disconnecting client...')
        if self.http_client:
            await self.http_client.close()
        await self.client.disconnect()

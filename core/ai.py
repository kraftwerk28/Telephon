import re
from typing import (
    Callable, List, Any, Union, AnyStr, Tuple,
    Awaitable, Optional, Pattern, Dict
)
from telethon import events, TelegramClient, tl
from dataclasses import dataclass
from aiohttp import ClientSession
from asyncio import AbstractEventLoop
import logging as log

from .context import TgAIContext
from .state import State
from .utils import *

TgAICallback = Tuple[
    Callable[[events.common.EventBuilder], Awaitable[bool]],
    Callable[[TgAIContext], None],
    Callable[[TgAIContext], Any],
]


class TgAI(object):
    def __init__(self, session_path: str, api_id: str, api_hash: str):
        self._callbacks: List[TgAICallback] = []
        self._del_callbacks: List[TgAICallback] = []
        # TODO: implement
        self.config: Any = None
        client = TelegramClient(session_path, api_id, api_hash)

        self.client: TelegramClient = client
        self.http_client: ClientSession = ClientSession(loop=client.loop)
        self.state = State.restore()

        client.add_event_handler(self._on_message, events.NewMessage)
        client.add_event_handler(self._on_delete, events.MessageDeleted)

        log.basicConfig(
            format='[%(asctime)s] %(message)s',
            datefmt='%d.%m.%Y %H:%M:%S',
            level=log.INFO
        )

    def on_command(
        self,
        command: Union[str, List[str]],
        argcount: int = 0,
        arglist: List[str] = [],
        direction: MsgDir = MsgDir.BOTH
    ):
        async def test(context: TgAIContext) -> bool:
            msg = context.event.message

            if not context.has_words():
                return False

            if (
                direction == MsgDir.OUT and not msg.out or
                direction == MsgDir.IN and msg.out
            ):  # Test message direction
                return False

            maybe_command = context.first_word()[COMMAND_PREFIX.__len__():]
            if (
                type(command) == str and maybe_command != command or
                maybe_command not in command
            ):  # Test command matching
                return False
            return True

        def preprocess(context):
            context.next_word()
            if arglist:
                al = context.n_words(arglist.__len__())
            else:
                al = context.n_words(argcount)

            if arglist:
                context.named_args = {k: al[i] for i, k in enumerate(arglist)}
            else:
                context.args = al

        def wrapper(func):
            self._callbacks.append((test, preprocess, func))

        return wrapper

    def on_text(
        self,
        pattern: Union[str, Pattern[AnyStr]],
        direction=MsgDir.BOTH
    ):
        pass

    def on_media(self, direction=MsgDir.BOTH, media_types: List[Any] = []):
        pass

    def on_delete(self):
        '''When message is deleted'''

        async def test(context: TgAIContext) -> bool:
            # TODO: implement
            return True

        def wrapper(func):
            self._del_callbacks.append((test, func))

        return wrapper

    async def _on_message(self, event):
        '''Event handler for telethon internal usage'''
        context = TgAIContext(
            self.client,
            event,
            state=self.state,
            http_client=self.http_client
        )

        for test, preprocess, func in self._callbacks:
            passed = await test(context)
            if passed:
                preprocess(context)
                await func(context)

        for defer_cb in context._deferred:
            defer_cb(context)

    async def _on_delete(self, event):
        context = TgAIContext(self.client, event, state=self.state)
        for test, func in self._del_callbacks:
            if await test(context):
                await func(context)

    async def _run_client(self):
        await self.client.start()
        log.info('Client started')
        await self.client.run_until_disconnected()

    def start(self, loop: Optional[AbstractEventLoop] = None):
        loop = self.client.loop
        try:
            loop.run_until_complete(self._run_client())
        except KeyboardInterrupt:
            loop.run_until_complete(self.shutdown())
        finally:
            loop.close()
            log.info('Client loop closed')
        return 0

    async def shutdown(self):
        self.client.remove_event_handler(self._on_message)
        self.client.remove_event_handler(self._on_delete)
        log.info('Disconnecting client')
        if self.http_client:
            await self.http_client.close()
        await self.client.disconnect()

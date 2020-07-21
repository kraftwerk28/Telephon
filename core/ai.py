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
from .command import CommandExecutor, Command


'''
### Must define a reaction - they will be returned from customer callbacks
e.g.:
@on_command('cmd')
async def on_cmd(ctx: Context):
    ...
    return reactions.Base('some text', cleanup_command=True,)
    OR
    return reactions.Photo('file.png')

### command args:
1, 2, 3 - meaningful
None - undefined (probably infinite)
0 - just 0, rarely used

### Every middleware can:
- modify Context (which has reference to instance's state and so on)
- return reaction, which does a lot of work for us (for example, reply to message, clean command message etc)
'''


class TgAI:
    def __init__(self, init_config: InitConfig):
        self._callbacks: List[TgAICallback] = []
        self._del_callbacks: List[TgAICallback] = []
        self.commands = []
        # TODO: implement
        self.config: Any = None
        client = TelegramClient(
            init_config.session_path,
            init_config.api_id,
            init_config.api_hash
        )

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
        args: int = 0,
        named_args: List[str] = [],
        direction: MsgDir = MsgDir.BOTH
    ):
        def wrapper(func):
            cmdcfg = Command(command, args, named_args, direction, func)
            self.commands.append(cmdcfg)
        return wrapper

    def on_text(
        self,
        pattern: Union[str, Pattern[AnyStr]],
        direction=MsgDir.BOTH
    ):
        pass

    def on_event(self):
        pass

    def on_media(self, direction=MsgDir.BOTH, media_types: List[Any] = []):
        pass

    def on_delete(self):
        '''When message is deleted'''
        def wrapper(func):
            pass
        return wrapper

    async def _run_commands(self, event):
        await CommandExecutor(self, event).execute()

    async def _on_message(self, event):
        '''Event handler for telethon internal usage'''
        await self._run_commands(event)

    async def _on_delete(self, event):
        pass

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

import os
import re
from typing import (Callable, List, Any, Union, AnyStr, Tuple,
                    Awaitable, Optional, Pattern, Dict)
from telethon import events, TelegramClient, tl
from dataclasses import dataclass
from aiohttp import ClientSession
from asyncio import AbstractEventLoop
import logging as log

from .base import TelephonBase
from .context import Context
from .state import State
from .command import CommandExecutor, Command
from .utils import InitConfig


"""
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
- return reaction, which does a lot of work for us
  (for example, reply to message, clean command message etc)
"""


class Telephon(TelephonBase):
    def __init__(self, init_config: InitConfig = None):
        if init_config is None:
            API_ID = os.getenv('API_ID')
            API_HASH = os.getenv('API_HASH')
            SESSION_PATH = os.path.abspath('./.sessions/tgai28')
            init_config = InitConfig(SESSION_PATH, API_ID, API_HASH)
        super(Telephon, self).__init__(init_config)

        self.commands: List[Command] = []
        # TODO: implement
        self.config: Any = None
        self.state = State.restore()

        self.client.add_event_handler(self._on_message, events.NewMessage)
        self.client.add_event_handler(self._on_delete, events.MessageDeleted)

    def on_command(self, *args, **kwargs):
        """
        Decorator for command handling
        """
        def wrapper(callback):
            cmdcfg = Command(*args, **kwargs, callback=callback)
            self.commands.append(cmdcfg)
        return wrapper

    def on_text(self, pattern: Union[str, Pattern[AnyStr]]):
        pass

    def on_event(self):
        pass

    def on_media(self, media_types: List[Any] = []):
        pass

    def on_delete(self):
        """When message is deleted"""
        def wrapper(func):
            pass
        return wrapper

    async def shutdown(self):
        await super().shutdown()
        self.client.remove_event_handler(self._on_message)
        self.client.remove_event_handler(self._on_delete)

    async def _run_commands(self, event):
        """Ran by `_on_message` method"""
        executor = CommandExecutor(self, event)
        await executor.execute()

    async def _on_message(self, event):
        """Event handler for telethon internal usage"""
        await self._run_commands(event)

    async def _on_delete(self, event):
        # Perform auto removing messages
        ids = [id for id in event.deleted_ids if id in self.state.autorm]
        for id in ids:
            chat_id, msg_id = self.state.autorm[id]
            await self.client.delete_messages(chat_id, msg_id)
            del self.state.autorm[id]
        log.info(self.state.autorm)

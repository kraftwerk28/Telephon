import re
import sys
from typing import Callable, List, Union
from dataclasses import dataclass
from telethon.events import NewMessage

from ..types import *
from .errors import *
from ..constants import *


@dataclass
class Command:
    command: Union[str, List[str]]
    args: int = None
    named_args: List[str] = None
    allow_incoming: bool = False
    only_incoming: bool = False
    callback: Callable[['Context'], Awaitable[None]] = None
    description: str = None

    def matches(self, token: str, event: NewMessage):
        msg = event.message
        if not hasattr(msg, 'text'):
            return False
        if self.only_incoming and msg.out:
            return False
        if not self.only_incoming and not self.allow_incoming and not msg.out:
            return False

        return self._matches_token(token)


    def _matches_token(self, token: str) -> bool:
        commandstr = re.sub(fr'^{COMMAND_PREFIX}', '', token)
        if type(self.command) == str:
            return commandstr == self.command
        elif type(self.command) in (tuple, list):
            return commandstr in self.command
        else:
            raise CommandException('Inconsistent type for '
                                   'command definition '
                                   f'{type(self.command)}.')

    def __repr__(self):
        command_repr = (self.command
                        if type(self.command == str)
                        else ', '.join(self.command))
        return (f'Command: {command_repr}; '
                f'args number: {self.args}; '
                f'named_args: {self.named_args}')

    def __call__(self, context: 'Context'):
        return self.callback(context)

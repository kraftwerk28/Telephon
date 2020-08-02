import re
import sys
from typing import Callable, List, Union
from .types import *

COMMAND_PREFIX = r'\.'
SUBCMD_LEFT_BRACKET = r'\['
SUBCMD_RIGHT_BRACKET = r'\]'
CMD_SPLIT_REGEX = re.compile(
    '|'.join([r'\s+',
              fr'({SUBCMD_LEFT_BRACKET})',
              fr'({SUBCMD_RIGHT_BRACKET})']))


class CommandException(Exception):
    pass


class Command:
    def __init__(self,
                 command: Union[str, List[str]],
                 args: int = None,
                 named_args: List[str] = [],
                 allow_incoming=False,
                 only_incoming=False,
                 callback=None):
        self.command: Union[str, List[str]] = command
        self.args: int = args
        self.named_args: List[str] = named_args
        self.allow_incoming: bool = allow_incoming
        self.only_incoming: bool = only_incoming
        self.callback = callback

    def __eq__(self, command: str) -> bool:
        commandstr = re.sub(fr'^{COMMAND_PREFIX}', '', command)
        if type(self.command) == str:
            return commandstr == self.command
        elif type(self.command) in (tuple, list):
            return commandstr in self.command
        else:
            raise CommandException('Inconsistent type for command definition'
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


class CommandExecutor:
    def __init__(self, telephon: 'Telephon', event):
        self._telephon = telephon
        self._event = event

    async def execute(self):
        msg = self._event.message
        text = msg.text
        tokens = [word for word in re.split(CMD_SPLIT_REGEX, text) if word]
        commands = self._telephon.commands
        while tokens:
            token = tokens.pop(0)
            if re.match(fr'^{COMMAND_PREFIX}\w+', token) is not None:
                matched = [
                    command for command in self._telephon.commands
                    if command == token
                ]
                for cmd in matched:
                    await self._execute_command(cmd, tokens)

            elif token == SUBCMD_LEFT_BRACKET:
                # TODO: implement nested commands
                pass

            elif token == SUBCMD_RIGHT_BRACKET:
                # TODO: implement nested commands
                pass

    async def _execute_command(self, command: Command, tokens: List[str]):
        args, named_args = None, None
        if command.named_args is not None:
            arglist = []
            for argname in command.named_args:
                arglist.append((argname, tokens.pop(0) if tokens else None))
            named_args = dict(arglist)
        else:
            args = []
            argcount = command.args
            if command.args > 0:
                for _ in range(argcount):
                    args.append(tokens.pop(0) if tokens else None)
            else:
                while tokens:
                    args.append(tokens.pop(0))

        print(f'args: {args}; named args: {named_args}')
        ctx = Context(self._telephon, self._event)
        await command(ctx)
        # if reaction is not None:
        #     await reaction(ctx)

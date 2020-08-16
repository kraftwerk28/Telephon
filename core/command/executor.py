import re
from typing import List

from ..types import *
from ..constants import *
from .command import Command


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
                matched: List[Command] = [
                    command for command in self._telephon.commands
                    if command.matches(token, self._event)
                ]
                print('Matched:', matched)
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
        elif command.args is not None:
            args = []
            argcount = command.args
            if command.args > 0:
                for _ in range(argcount):
                    args.append(tokens.pop(0) if tokens else None)
            else:
                while tokens:
                    args.append(tokens.pop(0))

        print(f'args: {args}; named args: {named_args}')
        ctx = Context(self._telephon, self._event, args, named_args)
        await command(ctx)

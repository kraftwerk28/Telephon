import re
from typing import Callable, List, Union
from .types import *
from .utils import MsgDir


COMMAND_PREFIX = r'\.'
SUBCMD_LEFT_BRACKET = r'\['
SUBCMD_RIGHT_BRACKET = r'\]'
CMD_SPLIT_REGEX = re.compile(
    '|'.join([
        fr'({COMMAND_PREFIX}\w+)',
        r'\s+',
        fr'({SUBCMD_LEFT_BRACKET})',
        fr'({SUBCMD_RIGHT_BRACKET})',
    ])
)


class Command:
    def __init__(
        self,
        command: Union[str, List[str]],
        args: int = None,
        named_args: List[str] = [],
        direction=MsgDir.BOTH,
        func=None,
    ):
        self.command = command
        self.args = args
        self.named_args: List[str] = named_args
        self.func = func

    def equals(self, command: str) -> bool:
        commandstr = re.sub(fr'^{COMMAND_PREFIX}', '', command)
        if type(self.command) == str:
            return commandstr == self.command
        elif type(self.command) in (tuple, list):
            return commandstr in self.command

    def __repr__(self):
        return (
            f'Command: {self.command}; '
            f'args: {self.args}; '
            f'named_args: {self.named_args}'
        )


class CommandExecutor:
    def __init__(self, tgai: 'TgAI', event):
        self._tgai = tgai
        self._event = event

    async def execute(self):
        msg = self._event.message
        text = msg.text
        tokens = [word for word in re.split(CMD_SPLIT_REGEX, text) if word]
        print('Tokens:', tokens)
        commands = self._tgai.commands
        while tokens:
            token = tokens.pop(0)
            if re.match(fr'^{COMMAND_PREFIX}\w+$', token) is not None:
                print('Token is command')
                matched = self._match_commands(token)
                print(matched)
                for cmd in matched:
                    await self._execute_one(cmd, tokens)

            elif token == SUBCMD_LEFT_BRACKET:
                # TODO: implement
                pass

            elif token == SUBCMD_RIGHT_BRACKET:
                # TODO: implement
                pass

    def _match_commands(self, command_str: str) -> List[Command]:
        return [cmd for cmd in self._tgai.commands if cmd.equals(command_str)]

    async def _execute_one(self, command: Command, tokens: List[str]):
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
        # Create context and run command with it:
        ctx = TgAIContext(self._tgai, self._event)

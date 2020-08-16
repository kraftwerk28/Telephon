from telethon import events, TelegramClient, tl
from typing import (List, Dict, Optional)
import re

from .state import State


class Context:
    """
    Token list (split by whitespace)
    acquire token from context (cut first word from token list)

    Must contain:
    text: whole text from arguments
    arglist: same as text, but separated
    Of course, client and event (message and so on)
    """

    def __init__(self,
                 telephon: 'Telephon',
                 event: events.common.EventCommon,
                 args: List[str] = None,
                 named_args: Dict[str, str] = None):
        self.client: TelegramClient = telephon.client
        self.event: events.common.EventCommon = event
        self.args = args
        self.named_args = named_args
        self.msg: tl.custom.Message = None

        if hasattr(event, 'message'):
            self.msg = event.message

    async def reply(self,
                    text: str,
                    photo: str = None,
                    delete_command_message=False,
                    reply=False,
                    send_to_saves=False,
                    **kwargs):
        """
        :param photo: file path to photo
        """
        msg, client = self.msg, self.client
        rest_kwargs = {'parse_mode': 'HTML'}

        if msg.out and delete_command_message:
            await msg.delete()

        if send_to_saves:
            await client.send_message('me', text, **rest_kwargs, **kwargs)
        elif reply:
            await msg.reply(text, **rest_kwargs, **kwargs)
        else:
            await msg.respond(text, **rest_kwargs, **kwargs)

    async def edit(self,
                   in_place=False):
        pass

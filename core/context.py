from asyncio import AbstractEventLoop
from aiohttp import ClientSession
from dataclasses import dataclass
import logging as log
from telethon import events, TelegramClient, tl
from typing import (Callable, List, Any, Union, AnyStr, Tuple,
                    Awaitable, Optional, Pattern, Dict, Set)
import re

from .state import State


class Context:
    '''
    Token list (split by whitespace)
    acquire token from context (cut first word from token list)

    Must contain:
    text: whole text from arguments
    arglist: same as text, but separated
    Of course, client and event (message and so on)
    '''

    def __init__(self,
                 telephon: 'Telephon',
                 event: events.common.EventCommon,
                 args: List[str] = None,
                 named_args: Dict[str, str] = None):
        self.client: TelegramClient = telephon.client
        self.event: events.common.EventCommon = event
        self.args = args
        self.named_args = named_args

        if isinstance(event, events.NewMessage):
            self.msg: tl.custom.Message = event.message

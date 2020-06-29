import re
from typing import (
    Callable, List, Any, Union, AnyStr, Tuple,
    Awaitable, Optional, Pattern, Dict, Set
)
from telethon import events, TelegramClient, tl
from dataclasses import dataclass
from aiohttp import ClientSession
from asyncio import AbstractEventLoop
import logging as log

from .state import State
from .deferrer import Deferrer


class TgAIContext(object):
    '''
    Token list (split by whitespace)
    acquire token from context (cut first word from token list)

    Must contain:
    text: whole text from arguments
    arglist: same as text, but separated
    Of course, client and event (message and so on)
    '''

    def __init__(
        self,
        client: TelegramClient,
        event: events.common.EventBuilder,
        **kwargs,
    ):
        self.client: TelegramClient = client
        self.event: events.common.EventCommon = event

        if hasattr(event, 'message'):
            self.msg: tl.custom.Message = event.message
            self._wordlist: List[str] = (event.message.text or '').split()
            self._wordlistgen = (w for w in self._wordlist)

        self._deferred: Set[Deferrer] = set()
        self.args: List[str] = []
        self.named_args: Dict[str, str] = {}
        self.__dict__.update(kwargs)

    def next_word(self) -> Optional[str]:
        if self._wordlist:
            return self._wordlist.pop(0)

    def first_word(self) -> Optional[str]:
        return self._wordlist[0] if self._wordlist else None

    def get_command(self) -> Optional[str]:
        w = self.first_word()
        if w.startswith(COMMAND_PREFIX):
            return self.next_word()[1:]

    def n_words(self, count: int) -> List[str]:
        '''
        If count > -1, give {count} arguments
        Otherwise, fetch all words (inf)
        '''
        words = []
        is_inf = count < 0
        while True if is_inf else count > 0:
            w = self.next_word()
            count -= 1
            if w:
                words.append(w)
            else:
                if is_inf:
                    break
                words.append(None)
        return words

    def has_words(self):
        return self._wordlist.__len__() > 0

    def defer(self, deferrer):
        self._deferred.add(deferrer)

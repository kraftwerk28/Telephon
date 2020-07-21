from typing import Callable, Awaitable, Tuple, Any
from telethon import events
from .context import TgAIContext


TgAICallback = Tuple[
    Callable[[events.common.EventBuilder], Awaitable[bool]],
    Callable[[TgAIContext], None],
    Callable[[TgAIContext], Any],
]

Middleware = Callable[['TgAIContext'], Awaitable[None]]

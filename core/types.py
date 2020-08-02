from typing import Callable, Awaitable, Tuple, Any
from telethon import events
from .context import Context


Middleware = Callable[['Context'], Awaitable[None]]

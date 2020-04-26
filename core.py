import re
from functools import reduce
from typing import Callable, List, Any, Union, AnyStr
from telethon import events, TelegramClient, tl


compose = lambda *funcs: lambda *args: reduce(
    lambda acc, fn: fn(*acc)
    if isinstance(acc, tuple)
    else fn(acc),
    funcs,
    args,
)


class Context(object):
    pass


class Composer(object):
    def __init__(self):
        self._callbacks = {}
        self._deferred = []

    def on(
        self,
        # command: Union[str, re.Pattern[AnyStr]],
        command: Any,
        *middlewares: Callable[[Context], Any],
    ):
        self._callbacks[command] = callback

    def get_callback(self):
        def cb(event: events.NewMessage):
            pass
        return cb


if __name__ == '__main__':
    def a(x, y): return 
    def b(x, y): 
    print(compose(a, b)(1, 2))

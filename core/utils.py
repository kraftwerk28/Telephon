from typing import List
from dataclasses import dataclass

COMMAND_PREFIX = '.'


class MsgDir:
    OUT = 0
    IN = 1
    BOTH = 2


@dataclass
class InitConfig:
    session_path: str
    api_id: str
    api_hash: str


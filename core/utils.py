from typing import List
from dataclasses import dataclass

@dataclass
class InitConfig:
    session_path: str
    api_id: str
    api_hash: str


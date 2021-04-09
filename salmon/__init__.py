import os
import nonebot
from nonebot.adapters.cqhttp import Bot
from typing import List


os.makedirs(os.path.expanduser('~/.salmon'), exist_ok=True)

def get_bot_list() -> List[Bot]:
    return list(nonebot.get_bots().values())


from . import R
from .service import Service
from .log import logger
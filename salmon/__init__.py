import os
import nonebot
from nonebot.adapters.cqhttp import Bot
from .log import new_logger
from . import configs

os.makedirs(os.path.expanduser('~/.salmon'), exist_ok=True)
logger = new_logger('salmon', configs.DEBUG)


from .log import error_handler, critical_handler
nonebot.logger.add(error_handler)
nonebot.logger.add(critical_handler)


def get_bot_list():
    return list(nonebot.get_bots().values())[0]


from . import R
from .service import Service
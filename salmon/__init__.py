import os
import nonebot
from nonebot.adapters.cqhttp import Bot
from typing import List
from . import configs


os.makedirs(os.path.expanduser('~/.salmon'), exist_ok=True)

def asgi():
    return nonebot.get_asgi()


def driver():
    return nonebot.get_driver()


def get_bot_list() -> List[Bot]:
    return list(nonebot.get_bots().values())


def init():
    nonebot.init()
    driver().register_adapter("cqhttp", Bot)
    for module_name in configs.MODULES_ON:
        nonebot.load_plugins(os.path.join(os.path.dirname(__file__), 'modules', module_name))


def run(app):
    nonebot.run(app=app)


from . import R
from .service import Service
from .log import logger
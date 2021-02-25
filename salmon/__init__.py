import os
import nonebot
from nonebot.adapters import Bot, Event, Message
from nonebot.adapters.cqhttp import Bot as CQHTTPBot
from .log import new_logger
from . import config

_bot = None
SalmonBot = Bot
os.makedirs(os.path.expanduser('~/.hoshino'), exist_ok=True)
logger = new_logger('hoshino', config.DEBUG)

def init() -> SalmonBot:
    global _bot
    nonebot.init(config)
    _bot = nonebot.get_bots()
    driver = nonebot.get_driver()
    driver.register_adapter("cqhttp", CQHTTPBot)
    config = driver.config
    from .log import error_handler, critical_handler
    nonebot.logger.addHandler(error_handler)
    nonebot.logger.addHandler(critical_handler)
    for plugin_name in config.PLUGINS_ON:
        nonebot.load_plugins(
            os.path.join(os.path.dirname(__file__), 'plugins', plugin_name),
            f'salmon.plugins.{plugin_name}')
    return _bot


def get_bot() -> SalmonBot:
    if _bot is None:
        raise ValueError('HoshinoBot has not been initialized')
    return _bot


def getBot() -> SalmonBot:
    return list(nonebot.get_bots().values())[0]


from . import R
from .service import Service, sucmd
import os
import nonebot
from nonebot import plugin
from nonebot.adapters import Bot
from nonebot.adapters.cqhttp import Bot as CQHTTPBot
from .log import new_logger
from . import configs

_bot = None
SalmonBot = Bot
os.makedirs(os.path.expanduser('~/.hoshino'), exist_ok=True)
logger = new_logger('salmon', configs.DEBUG)
plugins = 'salmon/plugins/'
configs = 'salmon/configs/'
nonebot.init()
driver = nonebot.get_driver()
driver.register_adapter('cqhttp', Bot)
config = driver.config
nonebot.load_plugins(configs)
from .log import error_handler, critical_handler
nonebot.logger.add(error_handler)
nonebot.logger.add(critical_handler)
for plugin_name in configs.PLUGINS_ON:
    module = os.path.join(plugins, plugin_name)
    nonebot.load_plugins(plugin_name)


def get_bot() -> SalmonBot:
    if _bot is None:
        raise ValueError('SalmonBot has not been initialized')
    return _bot


def get_bot_list() -> SalmonBot:
    return list(nonebot.get_bots().values())[0]
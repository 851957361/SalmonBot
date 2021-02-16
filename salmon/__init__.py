import nonebot
from nonebot.adapters import Bot, Event, Message
from .log import new_logger

logger = new_logger('salmon')

def getBot() -> Bot:
    return list(nonebot.get_bots().values())[0]
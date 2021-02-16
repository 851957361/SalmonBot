import nonebot
import asyncio
from nonebot.adapters.cqhttp import Bot as CQHTTPBot

nonebot.init()
driver = nonebot.get_driver()
app = nonebot.get_asgi()
driver.register_adapter("cqhttp", CQHTTPBot)
nonebot.load_builtin_plugins()
nonebot.load_plugins("salmon/plugins")

if __name__ == "__main__":
    nonebot.run()
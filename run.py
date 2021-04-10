import os
import nonebot
from nonebot.adapters.cqhttp import Bot as CQHTTPBot
from salmon import configs

modules = 'salmon/modules/'

nonebot.init()
driver = nonebot.get_driver()
app = nonebot.get_asgi()
driver.register_adapter('cqhttp', CQHTTPBot)
config = driver.config
for module_name in configs.MODULES_ON:
    module_name = os.path.join(modules, module_name)
    nonebot.load_plugins(module_name)


if __name__ == "__main__":
    nonebot.run()
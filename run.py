import os
import nonebot
from nonebot.adapters.cqhttp import Bot as CQHTTPBot
from salmon import configs

plugins = 'salmon/plugins/'

nonebot.init()
driver = nonebot.get_driver()
app = nonebot.get_asgi()
driver.register_adapter('cqhttp', CQHTTPBot)
config = driver.config
for plugin_name in configs.PLUGINS_ON:
    plugin_name = os.path.join(plugins, plugin_name)
    nonebot.load_plugins(plugin_name)


if __name__ == "__main__":
    nonebot.run()
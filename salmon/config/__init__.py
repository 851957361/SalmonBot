import os
import importlib
from .__bot__ import *
from nonebot.config import *
from salmon import log

# check correctness
RES_DIR = os.path.expanduser(RES_DIR)
assert RES_PROTOCOL in ('http', 'file', 'base64')

# load module configs
logger = log.new_logger('config', DEBUG)
for plugins in PLUGINS_ON:
    try:
        importlib.import_module('salmon.config.' + plugins)
        logger.info(f'Succeeded to load config of "{plugins}"')
    except ModuleNotFoundError:
        logger.warning(f'Not found config of "{plugins}"')
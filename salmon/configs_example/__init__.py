import os
import importlib
from .__bot__ import *
from nonebot.config import *
from salmon import log

# check correctness
RES_DIR = os.path.expanduser(RES_DIR)
assert RES_PROTOCOL in ('http', 'file', 'base64')

# load module configs
for modules in MODULES_ON:
    try:
        importlib.import_module('salmon.configs.' + modules)
        log.logger.info(f'Succeeded to load config of "{modules}"')
    except ModuleNotFoundError:
        log.logger.warning(f'Not found config of "{modules}"')
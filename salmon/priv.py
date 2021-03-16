BLACK = -999
DEFAULT = 0
NORMAL = 1
ADMIN = 2
OWNER = 3
WHITE = 5
SUPER = 9

from datetime import datetime
from nonebot.adapters.cqhttp import Bot
from nonebot.adapters.cqhttp.permission import GROUP, GROUP_ADMIN, GROUP_OWNER, PRIVATE
from nonebot.permission import SUPERUSER, Permission
from salmon.typing import CQEvent

OWNERS = SUPERUSER | GROUP_OWNER
ADMINS = SUPERUSER | GROUP_OWNER | GROUP_ADMIN
NORMALS = SUPERUSER | GROUP | PRIVATE

#===================== block list =======================#
_black_group = {}  # Dict[group_id, expr_time]
_black_user = {}  # Dict[user_id, expr_time]

def set_block_group(group_id, time):
    _black_group[group_id] = datetime.now() + time


def set_block_user(user_id, time):
    _black_user[user_id] = datetime.now() + time


def check_block_group(group_id):
    if group_id in _black_group and datetime.now() > _black_group[group_id]:
        del _black_group[group_id]  # 拉黑时间过期
        return False
    return bool(group_id in _black_group)


def check_block_user(user_id):
    if user_id in _black_user and datetime.now() > _black_user[user_id]:
        del _black_user[user_id]  # 拉黑时间过期
        return False
    return bool(user_id in _black_user)


def get_user_priv(bot: Bot, event: CQEvent):
    uid = event.user_id
    if uid in bot.config.superusers:
        return SUPER
    if check_block_user(uid):
        return BLACK
    role = event.sender.role
    if role == 'member':
        return NORMAL
    elif role == 'owner':
        return OWNER
    elif role == 'admin':
        return ADMIN
    elif role == 'administrator':
        return ADMIN    # for cqhttpmirai
    else:
        return NORMAL
            

def check_priv(bot: Bot, event: CQEvent, require: int) -> bool:
    return bool(get_user_priv(bot, event) >= require)
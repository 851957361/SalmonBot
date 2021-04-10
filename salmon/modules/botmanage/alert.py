from nonebot.plugin import on_notice
from nonebot.adapters.cqhttp import Event as CQEvent
from salmon import configs


@on_notice('group_decrease.kick_me')
async def kick_me(event: CQEvent):
    group_id = event.group_id
    operator_id = event.operator_id
    feed_back = configs.SUPERUSERS[0]
    await event.bot.send_private_msg(self_id=event.self_id, user_id=feed_back, message=f'已被用户{operator_id}踢出群聊{group_id}')
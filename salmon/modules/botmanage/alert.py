from nonebot.adapters.cqhttp.event import NoticeEvent
from nonebot.plugin import on_notice
from nonebot.adapters.cqhttp import NoticeEvent
from salmon import configs, Bot


kick_me = on_notice('group_decrease.kick_me')

@kick_me.handle()
async def kick_me_alert(bot: Bot, event: NoticeEvent):
    group_id = event.group_id
    operator_id = event.operator_id
    feed_back = configs.SUPERUSERS[0]
    await bot.send_private_msg(self_id=event.self_id, user_id=feed_back, message=f'已被用户{operator_id}踢出群聊{group_id}')
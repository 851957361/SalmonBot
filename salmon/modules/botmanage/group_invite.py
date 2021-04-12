from nonebot.plugin import on_request
from nonebot.adapters.cqhttp import GroupRequestEvent
from salmon import Bot, configs


group_invite = on_request()

@group_invite.handle()
async def handle_group_invite(bot: Bot, event: GroupRequestEvent):
    if event.user_id not in configs.SUPERUSERS:
        await group_invite.reject(reason='邀请入群请联系维护组')
    else:
        await group_invite.approve()       
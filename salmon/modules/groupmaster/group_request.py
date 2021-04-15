from nonebot.plugin import on_request
from nonebot.adapters.cqhttp import GroupRequestEvent
from salmon import Bot, configs


group_request = on_request()

@group_request.handle()
async def handle_group_invite(bot: Bot, event: GroupRequestEvent):
    if event.sub_type == 'invite':
        if event.user_id not in configs.SUPERUSERS:
            await group_request.reject(reason='邀请入群请联系维护组')
        else:
            await group_request.approve()
    elif event.sub_type == 'add':
        cfg = configs.groupmaster.join_approve
        gid = event.group_id
        if gid not in cfg:
            return
        for k in cfg[gid].get('keywords', []):
            if k in event.comment:
                await group_request.approve()
                return
        if cfg[gid].get('reject_when_not_match', False):
            await group_request.reject()
            return
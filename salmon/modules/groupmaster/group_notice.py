from nonebot.adapters.cqhttp import GroupIncreaseNoticeEvent, GroupDecreaseNoticeEvent
import salmon
from salmon import Service, Bot
from salmon.typing import Message


sv1 = Service('group-leave-notice', help_='退群通知')
sv2 = Service('group-welcome', help_='入群欢迎')

group_decrease = sv1.on_notice()
group_increase = sv2.on_notice()

@group_decrease.handle()
async def leave_notice(bot: Bot, event: GroupDecreaseNoticeEvent):
    if not event.is_tome():   
        user_info = await bot.get_stranger_info(user_id=event.user_id)
        nickname = user_info.get('nickname', '未知用户')
        await group_decrease.finish(f'{nickname}({event.user_id})退群了.')


@group_increase.handle()
async def increace_welcome(bot: Bot, event: GroupIncreaseNoticeEvent):
    if event.user_id == event.self_id:
        return  # ignore myself
    welcomes = salmon.configs.groupmaster.increase_welcome
    gid = event.group_id
    if gid in welcomes:
        await bot.send(event, welcomes[gid], at_sender=True)
    # elif 'default' in welcomes:
    #     await bot.send(event, welcomes[default], at_sender=True)
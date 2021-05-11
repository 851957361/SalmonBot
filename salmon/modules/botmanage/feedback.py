import salmon
from salmon import Bot, Service, priv
from salmon.typing import (CQEvent, GroupMessageEvent, Message,
                           PrivateMessageEvent, T_State)
from salmon.util import DailyNumberLimiter

sv = Service('_feedback_', manage_priv=priv.SUPERUSER, help_='[反馈] 后接反馈内容 联系维护组')

_max = 1
lmt = DailyNumberLimiter(_max)
EXCEED_NOTICE = f'您今天已经反馈过{_max}次了，请明早5点后再来！'

feed_back = sv.on_fullmatch('反馈', aliases={'来杯咖啡', '来杯红茶'}, only_group=False)

@feed_back.handle()
async def feed_rec(bot: Bot, event: CQEvent, state: T_State):
    uid = event.user_id
    user_info = await bot.get_stranger_info(user_id=uid)
    nickname = user_info.get('nickname', '未知用户')
    if not lmt.check(uid):
        if isinstance(event, GroupMessageEvent):
            await feed_back.finish(f'>{nickname}\n您今天已经反馈过{_max}次了，请明早5点后再来！')
        elif isinstance(event, PrivateMessageEvent):
            await feed_back.finish(EXCEED_NOTICE)
    lmt.increase(uid)
    args = event.get_message()
    if args:
        state['text'] = args
    if isinstance(event, GroupMessageEvent):
        message = f'>{nickname}\n请发送您要反馈的内容~'
    elif isinstance(event, PrivateMessageEvent):
        message = '请发送您要反馈的内容~'
    state['prompt'] = message

@feed_back.got('text', prompt='{prompt}')
async def feedback(bot: Bot, event: CQEvent, state: T_State):
    text = state['text']
    uid = event.user_id
    user_info = await bot.get_stranger_info(user_id=uid)
    nickname = user_info.get('nickname', '未知用户')
    su = salmon.configs.SUPERUSERS[0]
    if isinstance(event, GroupMessageEvent):
        await bot.send_private_msg(self_id=event.self_id, user_id=su, message=f'来自群聊{event.group_id}的{nickname}({uid})：\n========\n{text}')
        await bot.send(event, Message(f'>{nickname}\n您的反馈已发送至维护组！\n========\n{text}'))
    elif isinstance(event, PrivateMessageEvent):
        await bot.send_private_msg(self_id=event.self_id, user_id=su, message=f'{nickname}({uid})：\n========\n{text}')
        await bot.send(event, Message(f'您的反馈已发送至维护组！\n========\n{text}'))
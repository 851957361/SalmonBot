import salmon
from salmon import Service, priv, Bot
from salmon.typing import CQEvent, T_State, GroupMessageEvent, PrivateMessageEvent, Message
from salmon.util import DailyNumberLimiter


sv = Service('_feedback_', manage_priv=priv.SUPERUSER, help_='[反馈] 后接反馈内容 联系维护组')

_max = 1
lmt = DailyNumberLimiter(_max)
EXCEED_NOTICE = f'您今天已经反馈过{_max}次了，请明早5点后再来！'

feed_back = sv.on_fullmatch('反馈', aliases={'来杯咖啡', '来杯红茶'}, only_group=False)

@feed_back.handle()
async def feed_rec(bot: Bot, event: CQEvent, state: T_State):
    uid = event.user_id
    if not lmt.check(uid):
        if isinstance(event, GroupMessageEvent):
            at_sender = Message(f'[CQ:at,qq={event.user_id}]')
            await feed_back.finish(at_sender + EXCEED_NOTICE)
        elif isinstance(event, PrivateMessageEvent):
            await feed_back.finish(EXCEED_NOTICE)
    args = event.message.extract_plain_text()
    if args:
        state['text'] = args

@feed_back.got('text', prompt='请发送您要反馈的内容~')
async def feedback(bot: Bot, event: CQEvent, state: T_State):
    text = state['text']
    uid = event.user_id
    su = salmon.configs.SUPERUSERS[0]
    if isinstance(event, GroupMessageEvent):
        at_sender = f'[CQ:at,qq={uid}]'
        await bot.send_private_msg(self_id=event.self_id, user_id=su, message=f'群聊{event.group_id}@用户{uid}：\n{text}')
        await bot.send(event, Message(f'{at_sender}\n您的反馈已发送至维护组！\n======\n{text}'))
    elif isinstance(event, PrivateMessageEvent):
        await bot.send_private_msg(self_id=event.self_id, user_id=su, message=f'@用户{uid}：\n{text}')
        await bot.send(event, f'您的反馈已发送至维护组！\n======\n{text}')
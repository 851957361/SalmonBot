import re
import random
from salmon import Service, Bot
from salmon.typing import CQEvent, Message, T_State, GroupMessageEvent, PrivateMessageEvent


sv = Service('dice', help_='''
[.r] 掷骰子
[.r 3d12] 掷3次12面骰子
[.qj dihe] ケッコンカッコカリ
'''.strip())

async def do_dice(bot: Bot, event: CQEvent, num, min_, max_, opr, offset, TIP="的掷骰结果是："):
    if num == 0:
        await bot.send(event, '咦？骰子呢？')
        return
    min_, max_ = min(min_, max_), max(min_, max_)
    rolls = list(map(lambda _: random.randint(min_, max_), range(num)))
    sum_ = sum(rolls)
    rolls_str = '+'.join(map(lambda x: str(x), rolls))
    if len(rolls_str) > 100:
        rolls_str = str(sum_)
    res = sum_ + opr * offset
    msg = [
        f'{TIP}\n', str(num) if num > 1 else '', 'D',
        f'{min_}~' if min_ != 1 else '', str(max_),
        (' +-'[opr] + str(offset)) if offset else '',
        '=', rolls_str, (' +-'[opr] + str(offset)) if offset else '',
        f'={res}' if offset or num > 1 else '',
    ]
    msg = ''.join(msg)
    if isinstance(event, GroupMessageEvent):
        await bot.send(event, msg, at_sender=True)
    elif isinstance(event, PrivateMessageEvent):
        await bot.send(event, '您' + msg)


dice_roll = sv.on_rex(re.compile(r'^\.r\s*((?P<num>\d{0,2})d((?P<min>\d{1,4})~)?(?P<max>\d{0,4})((?P<opr>[+-])(?P<offset>\d{0,5}))?)?\b', re.I), only_group=False)
qj = sv.on_fullmatch('.qj', only_group=False)

@dice_roll.handle()
async def dice(bot: Bot, event: CQEvent, state: T_State):
    num, min_, max_, opr, offset = 1, 1, 100, 1, 0
    match = state['match']
    if s := match.group('num'):
        num = int(s)
    if s := match.group('min'):
        min_ = int(s)
    if s := match.group('max'):
        max_ = int(s)
    if s := match.group('opr'):
        opr = -1 if s == '-' else 1
    if s := match.group('offset'):
        offset = int(s)
    await do_dice(bot, event, num, min_, max_, opr, offset)


@qj.handle()
async def kc_marriage_rec(bot: Bot, event: CQEvent, state: T_State):
    wife = event.message.extract_plain_text().strip()
    if wife:
        tip = f'与{wife}的ケッコンカッコカリ结果是：'
    elif isinstance(event, GroupMessageEvent):
        tip = f'的ケッコンカッコカリ结果是：'
    elif isinstance(event, PrivateMessageEvent):
        tip = '您的ケッコンカッコカリ结果是：'
    await do_dice(bot, event, 1, 3, 6, 1, 0, tip)
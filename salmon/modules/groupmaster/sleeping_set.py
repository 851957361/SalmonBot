import math
import random
from salmon import Bot, Service, util
from salmon.typing import CQEvent


sv = Service('sleeping-set', help_='''
[精致睡眠] 8小时精致睡眠(bot需具有群管理权限)
[来一份精致昏睡下午茶套餐] 叫一杯先辈特调红茶(bot需具有群管理权限)
'''.strip())

sleep_8h = sv.on_fullmatch('精致睡眠', aliases={'睡眠套餐', '休眠套餐', '来一份精致睡眠套餐'}, only_group=True)
sleep = sv.on_rex(r'(来|來)(.*(份|个)(.*)(睡|茶)(.*))套餐', only_group=True)

@sleep_8h.handle()
async def set_8h(bot: Bot, event: CQEvent):
    await util.silence(bot, event, 8*60*60, skip_su=False)

@sleep.handle()
async def koucha(bot: Bot, event: CQEvent):
    base = 0 if '午' in event.get_plaintext() else 5*60*60
    length = len(event.get_plaintext())
    sleep_time = base + round(math.sqrt(length) * 60 * 30 + 60 * random.randint(-15, 15))
    await util.silence(bot, event, sleep_time, skip_su=False)
from salmon import Service, util, Bot, R
from salmon.typing import CQEvent, Message, GroupMessageEvent


sv = Service('antiqks', help_='识破骑空士的阴谋')

qks_url = "granbluefantasy.jp"
qksimg = R.img('antiqks.jpg').cqcode

@sv.on_keyword(qks_url)
async def _(bot: Bot, event: CQEvent):
    msg = Message(f'骑空士爪巴\n{qksimg}')
    if isinstance(event, GroupMessageEvent):
        at_sender = Message(f'[CQ:at,qq={event.user_id}]')
        await bot.send(event, at_sender + msg)
        await util.silence(bot, event, 60)
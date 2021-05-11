from salmon import Service, util, Bot, R
from salmon.typing import CQEvent, Message, GroupMessageEvent


sv = Service('antiqks', help_='识破骑空士的阴谋')

qks_url = "granbluefantasy.jp"
qksimg = R.img('antiqks.jpg').cqcode

@sv.on_keyword(qks_url)
async def _(bot: Bot, event: CQEvent):
    user_info = await bot.get_stranger_info(user_id=event.user_id)
    nickname = user_info.get('nickname', '未知用户')
    msg = Message(f'>{nickname}\n骑空士爪巴\n{qksimg}')
    if isinstance(event, GroupMessageEvent):
        await bot.send(event, msg)
        await util.silence(bot, event, 60)
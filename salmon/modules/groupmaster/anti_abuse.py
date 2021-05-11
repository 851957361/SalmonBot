import random
from datetime import timedelta
from nonebot.plugin import on_command
from nonebot.rule import to_me
from salmon import Bot, R, util, priv
import salmon
from salmon.typing import CQEvent, GroupMessageEvent, PrivateMessageEvent, Message


BANNED_WORD = {
    'rbq', 'RBQ', '憨批', '废物', '死妈', '崽种', '傻逼', '傻逼玩意',
    '没用东西', '傻B', '傻b', 'SB', 'sb', '煞笔', 'cnm', '爬', 'kkp',
    'nmsl', 'D区', '口区', '我是你爹', 'nmbiss', '弱智', '给爷爬', '杂种爬','爪巴'
}

anti_crit = on_command('ban_word', to_me(), aliases=BANNED_WORD)

@anti_crit.handle()
async def ban_word(bot: Bot, event: CQEvent):
    user_id = event.user_id
    user_info = await bot.get_stranger_info(user_id=user_id)
    nickname = user_info.get('nickname', '未知用户')
    salmon.logger.critical(f'Self: {event.self_id}, Message {event.message_id} from {user_id}: {event.message}')
    priv.set_block_user(user_id, timedelta(hours=8))
    pic = R.img(f"chieri{random.randint(1, 4)}.jpg").cqcode
    if isinstance(event, GroupMessageEvent):
        await bot.send(event, Message(f">{nickname}\n不理你啦！バーカー\n{pic}"))
        await util.silence(bot, event, 8*60*60)
    elif isinstance(event, PrivateMessageEvent):
        await bot.send(event, Message(f"不理你啦！バーカー\n{pic}"))
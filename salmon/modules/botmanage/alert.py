from nonebot.plugin import on_notice
from nonebot.adapters.cqhttp import GroupDecreaseNoticeEvent, GroupBanNoticeEvent, Event as CQEvent
import salmon
from salmon import configs, Bot, log 


driver = salmon.driver()
kick_me = on_notice()
ban_me = on_notice()

@driver.on_bot_connect
async def connect(bot: Bot):
    feed_back = configs.SUPERUSERS[0]
    await bot.send_private_msg(user_id=feed_back, message='ただいま戻りました、主さま')


@driver.on_bot_disconnect
async def disconnect(bot: Bot):
    feed_back = configs.SUPERUSERS[0]
    try:
        await bot.send_private_msg(user_id=feed_back, message='连接已断开，请检查服务器')
    except:
        log.logger.error("WebSocket连接已断开")


@kick_me.handle()
async def kick_me_alert(bot: Bot, event: GroupDecreaseNoticeEvent):
    if event.is_tome():
        group_id = event.group_id
        operator_id = event.operator_id
        if operator_id != event.self_id:    # ignore myself
            feed_back = configs.SUPERUSERS[0]
            user_info = await bot.get_stranger_info(user_id=operator_id)
            nickname = user_info.get('nickname', '未知用户')
            await bot.send_private_msg(self_id=event.self_id, user_id=feed_back, message=f'已被用户{nickname}({operator_id})移出群聊{group_id}')


@ban_me.handle()
async def ban_me_alert(bot: Bot, event: GroupBanNoticeEvent):
    if not event.is_tome():
        return
    if event.duration:
        group_id = event.group_id
        operator_id = event.operator_id
        feed_back = configs.SUPERUSERS[0]
        user_info = await bot.get_stranger_info(user_id=operator_id)
        nickname = user_info.get('nickname', '未知用户')
        await bot.send_private_msg(self_id=event.self_id, user_id=feed_back, message=f'已被群聊{group_id}的用户{nickname}({operator_id})禁言{event.duration}秒')
    else:
        group_id = event.group_id
        operator_id = event.operator_id
        feed_back = configs.SUPERUSERS[0]
        user_info = await bot.get_stranger_info(user_id=operator_id)
        nickname = user_info.get('nickname', '未知用户')
        await bot.send_private_msg(self_id=event.self_id, user_id=feed_back, message=f'已被解除群聊{group_id}的用户{nickname}({operator_id})的禁言')
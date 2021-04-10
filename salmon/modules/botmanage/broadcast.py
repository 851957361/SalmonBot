import asyncio
from nonebot.plugin import on_command
import salmon
from salmon import Bot, log
from salmon.typing import CQEvent, T_State


broadcast = on_command('broadcast', aliases={'bc', '广播'})

@broadcast.handle()
async def bc_rec(bot: Bot, event: CQEvent, state: T_State):
    if event.user_id not in salmon.configs.SUPERUSERS:
        await broadcast.finish('Insufficient authority.')
    msg = event.get_message()
    if msg:
        state['msg'] = msg

@broadcast.got('msg', prompt='请发送需要广播的内容')
async def bc(bot: Bot, event: CQEvent, state: T_State):
    msg = state['msg']
    for sid in bot.get_self_ids():
        gl = await bot.get_group_list(self_id=sid)
        gl = [ g['group_id'] for g in gl ]
        for g in gl:
            await asyncio.sleep(0.5)
            try:
                await bot.send_group_msg(self_id=sid, group_id=g, message=msg)
                log.logger.info(f'群{g} 投递广播成功')
            except Exception as e:
                log.logger.error(f'群{g} 投递广播失败：{type(e)}')
                try:
                    await bot.send(event, f'群{g} 投递广播失败：{type(e)}')
                except Exception as e:
                    log.logger.error(f'向广播发起者进行错误回报时发生错误：{type(e)}')
    await bot.send(event, f'广播完成！')
from nonebot.plugin import on_command
from salmon import Bot, configs
from salmon.typing import CQEvent, T_State, GroupMessageEvent, PrivateMessageEvent
from salmon.service import parse_gid


leave = on_command('quit', aliases={'退群'})

@leave.handle()
async def quit_rec(bot: Bot, event: CQEvent, state: T_State):
    if event.user_id not in configs.SUPERUSERS:
        await leave.finish('Insufficient authority.')
    if isinstance(event, GroupMessageEvent):
        state['gids'] = [event.group_id]
    elif isinstance(event, PrivateMessageEvent):
        gid = event.get_plaintext().split()
        if gid:
            state['gids'] = gid

@leave.got('gids', prompt='请输入需要退出的群聊群号', args_parser=parse_gid)
async def group_quit(bot: Bot, event: CQEvent, state: T_State):
    failed = []
    succ = []
    for gid in state['gids']:
        try:
            await bot.set_group_leave(self_id=event.self_id, group_id=gid)
            succ.append(gid)
        except:
            failed.append(gid)
    msg = f'已尝试退出{len(succ)}个群'
    if failed:
        msg += f"\n退出{len(failed)}个群失败：\n{failed}"
    su = configs.SUPERUSERS[0]
    await bot.send_private_msg(self_id=event.self_id, user_id=su, message=msg)
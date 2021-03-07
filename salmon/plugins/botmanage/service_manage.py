import re
from functools import cmp_to_key
from nonebot.rule import ArgumentParser
from nonebot.typing import T_State
from nonebot.plugin import on_shell_command
from nonebot.adapters.cqhttp import Event as CQEvent
from nonebot.adapters.cqhttp.event import GroupMessageEvent, PrivateMessageEvent
from nonebot.exception import FinishedException
from nonebot.permission import SUPERUSER
from salmon import Service, priv, Bot
from salmon.service import parse_gid

PRIV_TIP = f'群主={priv.OWNER}\n群管理={priv.ADMIN}\n群员/私聊={priv.NORMAL}\nbot维护组={priv.SUPERUSER}'
parser = ArgumentParser()
parser.add_argument('-a', '--all', action='store_true')
parser.add_argument('-h', '--hidden', action='store_true')

lssv = on_shell_command('lssv', aliases={'服务列表', '功能列表'}, permission=priv.ADMINS, parser=parser)
enable = on_shell_command('enable', aliases=('启用', '开启', '打开'))
disable = on_shell_command('disable', aliases=('禁用', '关闭'))

@lssv.handle()
async def _(bot: Bot, ev: CQEvent, state: T_State):
    if isinstance(ev, GroupMessageEvent):
        state['gids'] = [ev.group_id]

@lssv.got('gids', prompt='Usage: -g|--group <group_id> [-a|--all]', args_parser=parse_gid)
async def _(bot: Bot, ev: CQEvent, state: T_State):
    if not 'gids' in state:
        await bot.send(ev, 'Invalid input.')
        raise FinishedException
    verbose_all = state['args'].all
    svs = Service.get_loaded_services().values()
    for gid in state['gids']:
        msg = [f"群{gid}服务一览："]
        svs = map(lambda sv: (sv, sv.check_enabled(gid)), svs)
        key = cmp_to_key(lambda x, y: (y[1] - x[1]) or (-1 if x[0].name < y[0].name else 1 if x[0].name > y[0].name else 0))
        svs = sorted(svs, key=key)
        for sv, on in svs:
            if sv.visible or verbose_all:
                ox = 'O' if on else 'X'
                msg.append(f"|{ox}| {sv.name}")
        await lssv.finish('\n'.join(msg))


@enable.handle()
async def enable_service(bot: Bot, ev: CQEvent):
    await switch_service(ev, turn_on=True)

@disable.handle()
async def disable_service(bot: Bot, ev: CQEvent):
    await switch_service(ev, turn_on=False)

async def switch_service(bot: Bot, ev: CQEvent, turn_on:bool):
    action_tip = '启用' if turn_on else '禁用'
    if isinstance(ev, GroupMessageEvent):
        names = ev.get_plaintext().split()
        if not names:
            await bot.send(ev, f'空格后接要{action_tip}的服务名')
            raise FinishedException
        group_id = ev.group_id
        svs = Service.get_loaded_services()
        succ, notfound = [], []
        for name in names:
            if name in svs:
                sv = svs[name]
                u_priv = priv.get_user_priv(ev)
                if u_priv >= sv.manage_priv:
                    sv.set_enable(group_id) if turn_on else sv.set_disable(group_id)
                    succ.append(name)
                else:
                    await bot.send(ev, f'权限不足！{action_tip}{name}需要权限：{sv.manage_priv}，您的权限：{u_priv}\n{PRIV_TIP}')
                    raise FinishedException
            else:
                notfound.append(name)
        msg = []
        if succ:
            msg.append(f'已{action_tip}服务：' + '、'.join(succ))
        if notfound:
            msg.append('未找到服务：' + '、'.join(notfound))
        if msg:
            bot.send(ev, '\n'.join(msg))
    elif isinstance(ev, PrivateMessageEvent):
        if ev.group_id not in SUPERUSER:
            await bot.send(ev, f'请在群聊中{action_tip}服务')
            raise FinishedException
        args = ev.get_plaintext().split()
        if len(args) < 2:
            await bot.send(ev, 'Usage: <service_name> <group_id1> [<group_id2>, ...]')
            raise FinishedException
        name, *group_ids = args
        svs = Service.get_loaded_services()
        if name not in svs:
            await bot.send(ev, f'未找到服务：{name}')
            raise FinishedException
        sv = svs[name]
        succ = []
        for gid in group_ids:
            try:
                gid = int(gid)
                sv.set_enable(gid) if turn_on else sv.set_disable(gid)
                succ.append(gid)
            except:
                await bot.send(ev, f'非法群号：{gid}')
        await bot.send(ev, f'服务{name}已于{len(succ)}个群内{action_tip}：{succ}')
        raise FinishedException
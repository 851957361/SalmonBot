import nonebot
from functools import cmp_to_key
from nonebot.rule import ArgumentParser
from nonebot.typing import T_State
from nonebot.plugin import on_shell_command, on_command
from nonebot.adapters.cqhttp import Event as CQEvent
from nonebot.adapters.cqhttp.event import GroupMessageEvent, PrivateMessageEvent
from nonebot.adapters.cqhttp.message import Message
from nonebot.exception import FinishedException
import salmon
from salmon import Service, priv, Bot
from salmon.service import parse_gid

PRIV_TIP = f'群主={priv.OWNER}\n群管理={priv.ADMIN}\n群员/私聊={priv.NORMAL}\nbot维护组={priv.SUPER}'
parser = ArgumentParser()
parser.add_argument('-a', '--all', action='store_true')

lssv = on_shell_command('lssv', aliases={'服务列表', '功能列表'}, parser=parser)
enable = on_command('enable', aliases={'启用', '开启', '打开'})
disable = on_command('disable', aliases={'禁用', '关闭'})

@lssv.handle()
async def _(bot: Bot, event: CQEvent, state: T_State):
    if isinstance(event, GroupMessageEvent):
        state['gids'] = [event.group_id]

@lssv.got('gids', prompt='请输入需要查询的群号', args_parser=parse_gid)
async def _(bot: Bot, event: CQEvent, state: T_State):
    if not 'gids' in state:
        await bot.send(event, 'Invalid input.')
        raise FinishedException
    verbose_all = state['args'].all
    svs = Service.get_loaded_services().values()
    u_priv = priv.get_user_priv(bot, event)
    if u_priv >= 2:
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
    else:
        await bot.send(event, '查看服务列表需要管理及以上的权限')
        raise FinishedException


@enable.handle()
async def enable_service(bot: Bot, event: CQEvent):
    if isinstance(event, GroupMessageEvent):
        names = event.get_plaintext().split()
        uid = event.user_id
        at_sender = Message(f'[CQ:at,qq={uid}]')
        if not names:
            msg = at_sender + '请在空格后接要启用的服务名'
            await bot.send(event, msg)
            raise FinishedException
        group_id = event.group_id
        svs = Service.get_loaded_services()
        succ, notfound = [], []
        for name in names:
            if name in svs:
                sv = svs[name]
                u_priv = priv.get_user_priv(bot, event)
                if u_priv >= sv.manage_priv:
                    sv.set_enable(group_id)
                    succ.append(name)
                else:
                    await bot.send(event, at_sender + f'\n权限不足！启用[{name}]需要权限：{sv.manage_priv}，您的权限：{u_priv}\n{PRIV_TIP}')
                    raise FinishedException
            else:
                notfound.append(name)
        msg = []
        if succ:
            msg.append('已启用服务：' + '、'.join(succ))
        if notfound:
            msg.append('未找到服务：' + '、'.join(notfound))
        if msg:
            await bot.send(event, at_sender + '\n'.join(msg))
    elif isinstance(event, PrivateMessageEvent):
        if event.user_id not in salmon.configs.SUPERUSERS:
            await bot.send(event, f'请在群聊中启用服务')
            raise FinishedException
        args = event.get_plaintext().split()
        if len(args) < 2:
            await bot.send(event, 'Usage: <service_name> <group_id1> [<group_id2>, ...]')
            raise FinishedException
        name, *group_ids = args
        svs = Service.get_loaded_services()
        if name not in svs:
            await bot.send(event, f'未找到服务：{name}')
            raise FinishedException
        sv = svs[name]
        succ = []
        for gid in group_ids:
            try:
                gid = int(gid)
                sv.set_enable(gid)
                succ.append(gid)
            except:
                await bot.send(event, f'非法群号：{gid}')
        await bot.send(event, f'服务[{name}]已于{len(succ)}个群内启用：{succ}')
        raise FinishedException


@disable.handle()
async def disable_service(bot: Bot, event: CQEvent):
    if isinstance(event, GroupMessageEvent):
        names = event.get_plaintext().split()
        uid = event.user_id
        at_sender = Message(f'[CQ:at,qq={uid}]')
        if not names:
            msg = at_sender + '请在空格后接要禁用的服务名'
            await bot.send(event, msg)
            raise FinishedException
        group_id = event.group_id
        svs = Service.get_loaded_services()
        succ, notfound = [], []
        for name in names:
            if name in svs:
                sv = svs[name]
                u_priv = priv.get_user_priv(bot, event)
                if u_priv >= sv.manage_priv:
                    sv.set_disable(group_id)
                    succ.append(name)
                else:
                    await bot.send(event, at_sender + f'\n权限不足！禁用[{name}]需要权限：{sv.manage_priv}，您的权限：{u_priv}\n{PRIV_TIP}')
                    raise FinishedException
            else:
                notfound.append(name)
        msg = []
        if succ:
            msg.append('已禁用服务：' + '、'.join(succ))
        if notfound:
            msg.append('未找到服务：' + '、'.join(notfound))
        if msg:
            await bot.send(event, at_sender + '\n'.join(msg))
    elif isinstance(event, PrivateMessageEvent):
        if event.user_id not in salmon.configs.SUPERUSERS:
            await bot.send(event, f'请在群聊中禁用服务')
            raise FinishedException
        args = event.get_plaintext().split()
        if len(args) < 2:
            await bot.send(event, 'Usage: <service_name> <group_id1> [<group_id2>, ...]')
            raise FinishedException
        name, *group_ids = args
        svs = Service.get_loaded_services()
        if name not in svs:
            await bot.send(event, f'未找到服务：{name}')
            raise FinishedException
        sv = svs[name]
        succ = []
        for gid in group_ids:
            try:
                gid = int(gid)
                sv.set_disable(gid)
                succ.append(gid)
            except:
                await bot.send(event, f'非法群号：{gid}')
        await bot.send(event, f'服务[{name}]已于{len(succ)}个群内禁用：{succ}')
        raise FinishedException
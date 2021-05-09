from nonebot.plugin import on_command
from salmon import Bot, Service, configs
from salmon.typing import CQEvent, T_State


async def ls_group(bot: Bot, event: CQEvent):
    gl = await bot.get_group_list()
    msg = ["{group_id} {group_name}".format_map(g) for g in gl]
    msg = "\n".join(msg)
    msg = f"| 群号 | 群名 | 共{len(gl)}个群\n" + msg
    await bot.send(event, msg)


async def ls_friend(bot: Bot, event: CQEvent):
    gl = await bot.get_friend_list()
    msg = ["{user_id} {nickname}".format_map(g) for g in gl]
    msg = "\n".join(msg)
    msg = f"| QQ号 | 昵称 | 共{len(gl)}个好友\n" + msg
    await bot.send(event, msg)


async def ls_service(bot: Bot, event: CQEvent, service_name:str):
    all_services = Service.get_loaded_services()
    if service_name in all_services:
        sv = all_services[service_name]
        on_g = '\n'.join(map(lambda x: str(x), sv.enable_group))
        off_g = '\n'.join(map(lambda x: str(x), sv.disable_group))
        default_ = 'enabled' if sv.enable_on_default else 'disabled'
        msg = f"服务{sv.name}：\n默认：{default_}\nmanage_priv={sv.manage_priv}\nvisible={sv.visible}\n启用群：\n{on_g}\n禁用群：\n{off_g}"
        await bot.send(event, msg)
    else:
        await bot.send(event, f'未找到服务{service_name}')


lsg = on_command('ls -g', aliases={'ls -group'})
lsf = on_command('ls -f', aliases={'ls -friend'})
lss = on_command('ls -s', aliases={'ls -service'})

@lsg.handle()
async def ls_g(bot: Bot, event: CQEvent):
    if event.user_id not in configs.SUPERUSERS:
        await lsg.finish('Insufficient authority.')
    await ls_group(bot, event)

@lsf.handle()
async def ls_f(bot: Bot, event: CQEvent):
    if event.user_id not in configs.SUPERUSERS:
        await lsf.finish('Insufficient authority.')
    await ls_friend(bot, event)

@lss.handle()
async def ls_s(bot: Bot, event: CQEvent, state: T_State):
    if event.user_id not in configs.SUPERUSERS:
        await lss.finish('Insufficient authority.')
    args = event.get_plaintext().split()
    if args:
        state['service'] = args

@lss.got('service', prompt='请发送服务名')
async def ls_s(bot: Bot, event: CQEvent, state: T_State):
    service_name = state['service']
    await ls_service(bot, event, service_name)
from salmon import Service, priv, Bot
from salmon.typing import CQEvent
from nonebot.adapters.cqhttp.event import GroupMessageEvent, PrivateMessageEvent


sv = Service('_help_', manage_priv=priv.SUPER, visible=False)

TOP_MANUAL = '''
=====================
- SalmonBot使用说明 -
=====================
发送方括号[]内的关键词即可触发
※功能采取模块化管理，群管理可控制开关
[lssv] (群管理)查看所有功能开关
[来杯咖啡] 联系维护组
=====================
[帮助分组] 查看各功能分组
[帮助+分组名] 查看分组功能
[帮助+功能名] 查看功能帮助
[启用/禁用] (群管理)空格后接功能名
========
※除这里中写明外 另有其他隐藏功能:)
※隐藏功能属于赠品 不保证可用性
※本bot开源，可自行搭建
※服务器运行及开发维护需要成本，赞助支持请私戳作者
※您的支持是本bot更新维护的动力
※※调教时请注意使用频率，您的滥用可能会导致bot账号被封禁
'''.strip()

Bundle_help = '''
=====================
[pcr会战] pcr会战相关功能
[pcr查询] pcr相关查询功能
[pcr娱乐] 各种娱乐相关功能
[pcr订阅] pcr相关推送功能
[通用] 其他通用功能
=====================
[帮助+分组名] 查看分组功能
[帮助+功能名] 查看功能帮助
[启用/禁用] (群管理)空格后接功能名
'''.strip()

def get_bundle_manual(bundle_name, service_list, gid):
    manual = [bundle_name]
    service_list = sorted(service_list, key=lambda s: s.name)
    for sv in service_list:
        if sv.visible:
            manual.append(f"|{'○' if sv.check_enabled(gid) else '×'}| {sv.name}")
    return '\n'.join(manual)


def get_private_manual(bundle_name, service_list):
    manual = [bundle_name]
    service_list = sorted(service_list, key=lambda s: s.name)
    for sv in service_list:
        if sv.visible:
            manual.append(f"|※| {sv.name}")
    return '\n'.join(manual)
    

def get_service_help(name, service_info):
    manual = [f"➤{name}功能帮助："]
    service_info = sorted(service_info, key=lambda s: s.name)
    for sv in service_info:
        if sv.visible:
            if sv.help:
                manual.append(sv.help)
    return "\n".join(manual)


send_help = sv.on_fullmatch('help', aliases={'帮助'}, only_group=False)
help_bundle = sv.on_fullmatch('help_bundle', aliases={'帮助分组'}, only_group=False)


@send_help.handle()
async def help_handle(bot: Bot, event: CQEvent):
    name = event.get_plaintext().strip()
    bundles = Service.get_bundles()
    svs = Service.get_loaded_services()
    info = Service.get_help()
    if not name:
        await send_help.finish(TOP_MANUAL)
    elif name in bundles:
        if isinstance(event, GroupMessageEvent):
            msg = get_bundle_manual(name, bundles[name], event.group_id)
        elif isinstance(event, PrivateMessageEvent):
            msg = get_private_manual(name, bundles[name])
        await send_help.finish(msg)
    elif name in svs:
        msg = get_service_help(name, info[name])
        await send_help.finish(msg)


@help_bundle.handle()
async def help_bundle_handle(bot: Bot, event: CQEvent):
    await help_bundle.finish(Bundle_help)
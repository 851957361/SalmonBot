import re
import numpy as np
from salmon import Service, Bot, R, util
from salmon.typing import CQEvent, Message, T_State, GroupMessageEvent, PrivateMessageEvent


this_season = np.zeros(15001, dtype=int)
all_season = np.zeros(15001, dtype=int)

this_season[1:11] = 50
this_season[11:101] = 10
this_season[101:201] = 5
this_season[201:501] = 3
this_season[501:1001] = 2
this_season[1001:2001] = 2
this_season[2001:4000] = 1
this_season[4000:8000:100] = 50
this_season[8100:15001:100] = 15

all_season[1:11] = 500
all_season[11:101] = 50
all_season[101:201] = 30
all_season[201:501] = 10
all_season[501:1001] = 5
all_season[1001:2001] = 3
all_season[2001:4001] = 2
all_season[4001:7999] = 1
all_season[8100:15001:100] = 30


rank_jp = '20-4'
rank_tw = '19-3'
rank_cn = '12-5'
ptw = ' '.join(map(str, [
    R.img(f'priconne/quick/{rank_tw}_1.png').cqcode,
    R.img(f'priconne/quick/{rank_tw}_2.png').cqcode,
    R.img(f'priconne/quick/{rank_tw}_3.png').cqcode,
]))
pjp = ' '.join(map(str, [
    R.img(f'priconne/quick/{rank_jp}_1.png').cqcode,
    R.img(f'priconne/quick/{rank_jp}_2.png').cqcode,
    R.img(f'priconne/quick/{rank_jp}_3.png').cqcode,
]))
pcn = ' '.join(map(str, [
    R.img(f'priconne/quick/{rank_cn}_1.png').cqcode,
    R.img(f'priconne/quick/{rank_cn}_2.png').cqcode,
]))


YUKARI_SHEET = Message(f'''
{R.img('priconne/quick/黄骑充电.jpg').cqcode}
※大圈是1动充电对象 PvP测试
※黄骑四号位例外较多
※对面羊驼或中后卫坦 有可能歪
※我方羊驼算一号位
※图片搬运自漪夢奈特''')


sv_help = '''
[rank日服] rank推荐表
[rank台服] rank推荐表
[rank陆服] rank推荐表
[挖矿15001] 矿场余钻
[黄骑充电表] 黄骑1动规律
[谁是霸瞳] 角色别称查询
'''.strip()

sv = Service('pcr-query', help_=sv_help, bundle='pcr查询')

miner = sv.on_fullmatch('挖矿', aliases={'jjc钻石', '竞技场钻石', 'jjc钻石查询', '竞技场钻石查询'}, only_group=False)
rank = sv.on_fullmatch('rank', aliases={'Rank', 'rank表', 'Rank表'}, only_group=False)
yukari = sv.on_fullmatch('yukari-sheet', aliases={'黄骑充电', '酒鬼充电', '酒鬼充电表', '黄骑充电表'}, only_group=False)

@miner.handle()
async def miner_rec(bot: Bot, event: CQEvent, state: T_State):
    try:
        args = int(event.message.extract_plain_text())
        if args:
            state['rank'] = args
    except:
        pass

@miner.got('rank', prompt='请发送当前竞技场排名')
async def arena_miner(bot: Bot, event: CQEvent, state: T_State):
    rank = int(state['rank'])
    rank = np.clip(rank, 1, 15001)
    s_all = all_season[1:rank].sum()
    s_this = this_season[1:rank].sum()
    if 1 <= rank <= 15001:
      lst=[str(rank)+"→"]
      for _ in range(40):
       if 70 < rank <= 15001:
         rank = 0.85 * rank
         rank = int(rank // 1)
         lst.append(str(rank)+"→")
       elif 10 < rank <= 70:
         rank = int(rank - 10)
         lst.append(str(rank)+'→')
       elif 0 < rank <= 10:
         lst.append(1)
         break
    else:
        msg3 = "请输入15001以内的正整数"
        await miner.finish(msg3)
    if isinstance(event, GroupMessageEvent):
        at_sender = f'[CQ:at,qq={event.user_id}]'
        msg1 = Message(f"{at_sender}\n最高排名奖励还剩{s_this}钻\n历届最高排名还剩{s_all}钻\n推荐挖矿路径:\n")
    elif isinstance(event, PrivateMessageEvent):
        msg1 = f"最高排名奖励还剩{s_this}钻\n历届最高排名还剩{s_all}钻\n推荐挖矿路径:\n"
    msg2 = ''.join('%s' %id for id in lst)
    await bot.send(event, msg1 + msg2)


@rank.handle()
async def rank_rec(bot: Bot, event: CQEvent, state: T_State):
    args = util.normalize_str(event.get_plaintext().strip())
    if args:
        state['name'] = args

@rank.got('name', prompt='请发送需要查询rank表的区服')
async def rank_sheet(bot: Bot, event: CQEvent, state: T_State):
    name = util.normalize_str(state['name'])
    at_sender = f'[CQ:at,qq={event.user_id}]'
    if name in ('国', '国服', 'cn'):
        await rank.finish('请选择详细区服\n※例:"rank表b服"或"rank表台服"')
    elif name in ('b', 'b服', 'bl', 'bilibili', '陆', '陆服'):
        name = 'BL'
    elif name in ('台', '台服', 'tw', 'sonet'):
        name = 'TW'
    elif name in ('日', '日服', 'jp', 'cy', 'cygames'):
        name = 'JP'
    else:
        if isinstance(event, GroupMessageEvent):
            await rank.finish(Message(f'{at_sender}\n未知区服，请重新选择\n*rank表日服\n*rank表台服\n*rank表b服'))
        elif isinstance(event, PrivateMessageEvent):
            await rank.finish('未知区服，请重新选择\n*rank表日服\n*rank表台服\n*rank表b服')
    msg = ['表格仅供参考']
    if name == 'JP':
        msg.append(f'※不定期搬运自图中Q群\n※广告为原作者推广，与本bot无关\nR{rank_jp} rank表：\n{pjp}')
        # pos = match.group(3)
        # if not pos or '前' in pos:
        #     msg.append(str(p4))
        # if not pos or '中' in pos:
        #     msg.append(str(p5))
        # if not pos or '后' in pos:
        #     msg.append(str(p6))
        await bot.send(event, Message('\n'.join(msg)))
    elif name == 'TW':
        msg.append(f'※不定期搬运自漪夢奈特\n※详见油管频道\nR{rank_tw} rank表：\n{ptw}')
        await bot.send(event, Message('\n'.join(msg)))
    elif name == 'BL':
        msg.append(f'※不定期搬运自B站专栏\n※制作by席巴鸽\nR{rank_cn} rank表：\n{pcn}')
        await bot.send(event, Message('\n'.join(msg)))


@yukari.handle()
async def yukari_sheet(bot: Bot, event: CQEvent):
    at_sender = Message(f'[CQ:at,qq={event.user_id}]')
    if isinstance(event, GroupMessageEvent):
        await bot.send(event, at_sender + YUKARI_SHEET)
    elif isinstance(event, PrivateMessageEvent):
        await bot.send(event, YUKARI_SHEET)
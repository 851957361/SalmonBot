import os
import random
from collections import defaultdict
import salmon
from salmon import Service, Bot, priv, util, log
from salmon.util import DailyNumberLimiter, concat_pic, pic2b64
from salmon.typing import CQEvent, Message, MessageSegment, T_State, GroupMessageEvent, PrivateMessageEvent, FinishedException
from salmon.service import parse_uid
from salmon.modules.priconne.pcr_data import chara
from salmon.modules.priconne.pool import Gacha
try:
    import ujson as json
except:
    import json


gacha_help = '''
[来发十连] 转蛋模拟
[来发单抽] 转蛋模拟
[来一井] 3w钻！
[查看卡池] 模拟卡池&出率
[切换卡池] 更换模拟卡池
'''.strip()

sv = Service('gacha', bundle='pcr查询', help_=gacha_help)

jewel_limit = DailyNumberLimiter(6000)
tenjo_limit = DailyNumberLimiter(1)

JEWEL_EXCEED_NOTICE = f'您今天已经抽过{jewel_limit.max}钻了，欢迎明早5点后再来！'
TENJO_EXCEED_NOTICE = f'您今天已经抽过{tenjo_limit.max}张天井券了，欢迎明早5点后再来！'
POOL = ('MIX', 'JP', 'TW', 'BL')
DEFAULT_POOL = POOL[0]

_pool_config_file = os.path.expanduser('~/.salmon/group_pool_config.json')
_group_pool = {}
try:
    with open(_pool_config_file, encoding='utf8') as f:
        _group_pool = json.load(f)
except FileNotFoundError as e:
    log.logger.warning('group_pool_config.json not found, will create when needed.')
_group_pool = defaultdict(lambda: DEFAULT_POOL, _group_pool)

def dump_pool_config():
    with open(_pool_config_file, 'w', encoding='utf8') as f:
        json.dump(_group_pool, f, ensure_ascii=False)

    
gacha_10_aliases = ('抽十连', '十连', '十连！', '十连抽', '来个十连', '来发十连', '来次十连', '抽个十连', '抽发十连', '抽次十连', '十连扭蛋', '扭蛋十连',
                    '10连', '10连！', '10连抽', '来个10连', '来发10连', '来次10连', '抽个10连', '抽发10连', '抽次10连', '10连扭蛋', '扭蛋10连')
gacha_1_aliases = ('单抽', '单抽！', '来发单抽', '来个单抽', '来次单抽', '扭蛋单抽', '单抽扭蛋')
gacha_200_aliases = ('一井', '抽一井', '来一井', '来发井', '抽发井', '天井扭蛋', '扭蛋天井')
POOL_NAME_TIP = '请选择以下卡池\n> 切换卡池jp\n> 切换卡池tw\n> 切换卡池b\n> 切换卡池mix'

gacha_1 = sv.on_fullmatch('gacha-1', aliases=gacha_1_aliases, only_group=False)
gacha_10 = sv.on_fullmatch('gacha-10', aliases=gacha_10_aliases, only_group=False)
gacha_200 = sv.on_fullmatch('gacha-300', aliases=gacha_200_aliases, only_group=False)
gacha_pool = sv.on_fullmatch('look-up', aliases={'卡池资讯', '查看卡池', '看看卡池', '康康卡池', '看看up', '看看UP'}, only_group=False)
gacha_switch = sv.on_fullmatch('gacha-switch', aliases={'切换卡池', '选择卡池'}, only_group=False)
kakin = sv.on_fullmatch('kakin', aliases={'氪金', '课金'}, handlers=[parse_uid], only_group=False)

@gacha_pool.handle()
async def look_pool(bot: Bot, event: CQEvent):
    if isinstance(event, GroupMessageEvent):
        gid = str(event.group_id)
        gacha = Gacha(_group_pool[gid])
    elif isinstance(event, PrivateMessageEvent):
        name = util.normalize_str(event.get_plaintext().strip())
        if not name:
            await gacha_pool.finish('请后接区服简称\n※例:"查看卡池jp"')
        elif name in ('国', '国服', 'cn'):
            await gacha_pool.finish('请选择详细区服\n※例:"查看卡池b服"或"查看卡池台服"')
        elif name in ('b', 'b服', 'bl', 'bilibili', '陆', '陆服'):
            name = 'BL'
        elif name in ('台', '台服', 'tw', 'sonet'):
            name = 'TW'
        elif name in ('日', '日服', 'jp', 'cy', 'cygames'):
            name = 'JP'
        elif name in ('混', '混合', 'mix'):
            name = 'MIX'
        else:
            await gacha_pool.finish('未知区服，请接区服简称\n※例:"查看卡池jp"')
        gacha = Gacha(name)
    up_chara = gacha.up
    up_chara = map(lambda x: str(chara.fromname(x, star=3).icon.cqcode) + x, up_chara)
    up_chara = '\n'.join(up_chara)
    await gacha_pool.finish(Message(f"本期卡池主打的角色：\n{up_chara}\nUP概率合计={(gacha.up_prob/10):.1f}%\n3★出率={(gacha.s3_prob)/10:.1f}%"))


@gacha_switch.handle()
async def switch_recg(bot: Bot, event: CQEvent, state: T_State):
    user_info = await bot.get_stranger_info(user_id=event.user_id)
    nickname = user_info.get('nickname', '未知用户')
    if isinstance(event, PrivateMessageEvent):
        await gacha_switch.finish('请在群聊内切换卡池')
    elif isinstance(event, GroupMessageEvent):
        args = util.normalize_str(event.get_plaintext().strip())
        if args:
            state['name'] = args
        message = f'>{nickname}\n请发送需要切换的卡池的区服'
        state['prompt'] = message

@gacha_switch.got('name', prompt='{prompt}')
async def switch_pool(bot: Bot, event: CQEvent, state: T_State):
    if isinstance(event, GroupMessageEvent):
        user_info = await bot.get_stranger_info(user_id=event.user_id)
        nickname = user_info.get('nickname', '未知用户')
        if not priv.check_priv(bot, event, priv.ADMIN): 
            await gacha_switch.finish(f'>{nickname}\n只有群管理才能切换卡池')
        name = util.normalize_str(state['name'])
        if name in ('国', '国服', 'cn'):
            await gacha_pool.finish(f'>{nickname}\n请选择以下卡池\n> 选择卡池b服\n> 选择卡池台服')
        elif name in ('b', 'b服', 'bl', 'bilibili', '陆', '陆服'):
            name = 'BL'
        elif name in ('台', '台服', 'tw', 'sonet'):
            name = 'TW'
        elif name in ('日', '日服', 'jp', 'cy', 'cygames'):
            name = 'JP'
        elif name in ('混', '混合', 'mix'):
            name = 'MIX'
        else:
            await gacha_pool.finish(f'>{nickname}\n未知区服，{POOL_NAME_TIP}')
        gid = str(event.group_id)
        _group_pool[gid] = name
        dump_pool_config()
        await bot.send(event, f'>{nickname}\n卡池已切换为{name}池')
        await look_pool(bot, event)


async def check_jewel_num(bot: Bot, event: CQEvent):
    uid = event.user_id
    user_info = await bot.get_stranger_info(user_id=uid)
    nickname = user_info.get('nickname', '未知用户')
    if not jewel_limit.check(uid):
        if isinstance(event, GroupMessageEvent):
            sender = f'>{nickname}\n'
            await bot.send(event, sender + JEWEL_EXCEED_NOTICE)
        elif isinstance(event, PrivateMessageEvent):
            await bot.send(event, JEWEL_EXCEED_NOTICE)
        raise FinishedException


async def check_tenjo_num(bot: Bot, event: CQEvent):
    uid = event.user_id
    user_info = await bot.get_stranger_info(user_id=uid)
    nickname = user_info.get('nickname', '未知用户')
    if not tenjo_limit.check(uid):
        if isinstance(event, GroupMessageEvent):
            sender = f'>{nickname}\n'
            await bot.send(event, sender + TENJO_EXCEED_NOTICE)
        elif isinstance(event, PrivateMessageEvent):
            await bot.send(event, TENJO_EXCEED_NOTICE)
        raise FinishedException


@gacha_1.handle()
async def ichi_rec(bot: Bot, event: CQEvent, state: T_State):
    await check_jewel_num(bot, event)
    uid = event.user_id
    jewel_limit.increase(uid, 150)
    user_info = await bot.get_stranger_info(user_id=uid)
    nickname = user_info.get('nickname', '未知用户')
    if isinstance(event, GroupMessageEvent):
        gid = event.group_id
        gacha = Gacha(_group_pool[gid])
        chara, _ = gacha.gacha_one(gacha.up_prob, gacha.s3_prob, gacha.s2_prob)
        res = f'{chara.icon.cqcode} {chara.name} {"★"*chara.star}'
        await gacha_1.finish(Message(f'>{nickname}\n素敵な仲間が増えますよ！\n{res}'))
    elif isinstance(event, PrivateMessageEvent):
        args = util.normalize_str(event.get_plaintext().strip())
        if args:
            state['name'] = args

@gacha_1.got('name', prompt='请发送卡池的区服')
async def gacha_ichi(bot: Bot, event: CQEvent, state: T_State):
    if isinstance(event, PrivateMessageEvent):
        name = util.normalize_str(state['name'])
        if name in ('国', '国服', 'cn'):
            await gacha_1.finish('请选择详细区服\n※例:"来发单抽b服"或"来发单抽台服"')
        elif name in ('b', 'b服', 'bl', 'bilibili', '陆', '陆服'):
            name = 'BL'
        elif name in ('台', '台服', 'tw', 'sonet'):
            name = 'TW'
        elif name in ('日', '日服', 'jp', 'cy', 'cygames'):
            name = 'JP'
        elif name in ('混', '混合', 'mix'):
            name = 'MIX'
        else:
            await gacha_1.finish('未知区服，请接区服简称\n※例:"来发单抽jp"')
        gacha = Gacha(name)
        chara, _ = gacha.gacha_one(gacha.up_prob, gacha.s3_prob, gacha.s2_prob)
        res = f'{chara.icon.cqcode} {chara.name} {"★"*chara.star}'
        await gacha_1.finish(Message(f'素敵な仲間が増えますよ！\n{res}'))


@gacha_10.handle()
async def jyu_rec(bot: Bot, event: CQEvent, state: T_State):
    SUPER_LUCKY_LINE = 170
    await check_jewel_num(bot, event)
    uid = event.user_id
    user_info = await bot.get_stranger_info(user_id=uid)
    nickname = user_info.get('nickname', '未知用户')
    jewel_limit.increase(uid, 1500)
    if isinstance(event, GroupMessageEvent):
        gid = event.group_id
        gacha = Gacha(_group_pool[gid])
        result, hiishi = gacha.gacha_ten()
        res1 = chara.gen_team_pic(result[:5], star_slot_verbose=False)
        res2 = chara.gen_team_pic(result[5:], star_slot_verbose=False)
        res = concat_pic([res1, res2])
        res = pic2b64(res)
        res = MessageSegment.image(res)
        result = [f'{c.name}{"★"*c.star}' for c in result]
        res1 = ' '.join(result[0:5])
        res2 = ' '.join(result[5:])
        res = f'{res}\n{res1}\n{res2}'
        if hiishi >= SUPER_LUCKY_LINE:
            await bot.send(event, '恭喜海豹！おめでとうございます！')
        await gacha_10.finish(Message(f'>{nickname}\n素敵な仲間が増えますよ！\n{res}'))
    elif isinstance(event, PrivateMessageEvent):
        args = util.normalize_str(event.get_plaintext().strip())
        if args:
            state['name'] = args

@gacha_10.got('name', prompt='请发送卡池的区服')
async def gacha_jyu(bot: Bot, event: CQEvent, state: T_State):
    if isinstance(event, PrivateMessageEvent):
        name = util.normalize_str(state['name'])
        SUPER_LUCKY_LINE = 170
        if name in ('国', '国服', 'cn'):
            await gacha_10.finish('请选择详细区服\n※例:"来发十连b服"或"来发十连台服"')
        elif name in ('b', 'b服', 'bl', 'bilibili', '陆', '陆服'):
            name = 'BL'
        elif name in ('台', '台服', 'tw', 'sonet'):
            name = 'TW'
        elif name in ('日', '日服', 'jp', 'cy', 'cygames'):
            name = 'JP'
        elif name in ('混', '混合', 'mix'):
            name = 'MIX'
        else:
            await gacha_10.finish('未知区服，请接区服简称\n※例:"来发十连jp"')
        gacha = Gacha(name)
        result, hiishi = gacha.gacha_ten()
        res1 = chara.gen_team_pic(result[:5], star_slot_verbose=False)
        res2 = chara.gen_team_pic(result[5:], star_slot_verbose=False)
        res = concat_pic([res1, res2])
        res = pic2b64(res)
        res = MessageSegment.image(res)
        result = [f'{c.name}{"★"*c.star}' for c in result]
        res1 = ' '.join(result[0:5])
        res2 = ' '.join(result[5:])
        res = f'{res}\n{res1}\n{res2}'
        if hiishi >= SUPER_LUCKY_LINE:
            await bot.send(event, '恭喜海豹！おめでとうございます！')
        await gacha_10.finish(Message(f'素敵な仲間が増えますよ！\n{res}'))


@gacha_200.handle()
async def nibyaku_rec(bot: Bot, event: CQEvent, state: T_State):
    await check_tenjo_num(bot, event)
    uid = event.user_id
    user_info = await bot.get_stranger_info(user_id=uid)
    nickname = user_info.get('nickname', '未知用户')
    tenjo_limit.increase(uid)
    if isinstance(event, GroupMessageEvent):
        gid = event.group_id
        gacha = Gacha(_group_pool[gid])
        result = gacha.gacha_tenjou()
        up = len(result['up'])
        s3 = len(result['s3'])
        s2 = len(result['s2'])
        s1 = len(result['s1'])
        res = [*(result['up']), *(result['s3'])]
        random.shuffle(res)
        lenth = len(res)
        if lenth <= 0:
            res = "竟...竟然没有3★？！"
        else:
            step = 4
            pics = []
            for i in range(0, lenth, step):
                j = min(lenth, i + step)
                pics.append(chara.gen_team_pic(res[i:j], star_slot_verbose=False))
            res = concat_pic(pics)
            res = pic2b64(res)
            res = MessageSegment.image(res)
        msg = [
            f">{nickname}\n"
            f"素敵な仲間が増えますよ！ {res}",
            f"★★★×{up+s3} ★★×{s2} ★×{s1}",
            f"获得记忆碎片×{100*up}与女神秘石×{50*(up+s3) + 10*s2 + s1}！\n第{result['first_up_pos']}抽首次获得up角色" if up else f"获得女神秘石{50*(up+s3) + 10*s2 + s1}个！"
        ]
        if up == 0 and s3 == 0:
            msg.append("太惨了，咱们还是退款删游吧...")
        elif up == 0 and s3 > 5:
            msg.append("up呢？我的up呢？")
        elif up == 0 and s3 <= 2:
            msg.append("这位酋长，梦幻包考虑一下？")
        elif up == 0:
            msg.append("据说天井的概率只有12.16%")
        elif up <= 2:
            if result['first_up_pos'] < 50:
                msg.append("你的喜悦我收到了，滚去喂鲨鱼吧！")
            elif result['first_up_pos'] < 100:
                msg.append("已经可以了，您已经很欧了")
            elif result['first_up_pos'] > 190:
                msg.append("标 准 结 局")
            elif result['first_up_pos'] > 150:
                msg.append("补井还是不补井，这是一个问题...")
            else:
                msg.append("期望之内，亚洲水平")
        elif up == 3:
            msg.append("抽井母五一气呵成！多出30等专武～")
        elif up >= 4:
            msg.append("记忆碎片一大堆！您是托吧？")
        msg = Message('\n'.join(msg))
        await gacha_200.finish(msg)
    elif isinstance(event, PrivateMessageEvent):
        args = util.normalize_str(event.get_plaintext().strip())
        if args:
            state['name'] = args

@gacha_200.got('name', prompt='请发送卡池的区服')
async def gacha_nibyaku(bot: Bot, event: CQEvent, state: T_State):
    if isinstance(event, PrivateMessageEvent):
        name = util.normalize_str(state['name'])
        if name in ('国', '国服', 'cn'):
            await gacha_200.finish('请选择详细区服\n※例:"来一井b服"或"来一井台服"')
        elif name in ('b', 'b服', 'bl', 'bilibili', '陆', '陆服'):
            name = 'BL'
        elif name in ('台', '台服', 'tw', 'sonet'):
            name = 'TW'
        elif name in ('日', '日服', 'jp', 'cy', 'cygames'):
            name = 'JP'
        elif name in ('混', '混合', 'mix'):
            name = 'MIX'
        else:
            await gacha_200.finish('未知区服，请接区服简称\n※例:"来一井jp"')
        gacha = Gacha(name)
        result = gacha.gacha_tenjou()
        up = len(result['up'])
        s3 = len(result['s3'])
        s2 = len(result['s2'])
        s1 = len(result['s1'])
        res = [*(result['up']), *(result['s3'])]
        random.shuffle(res)
        lenth = len(res)
        if lenth <= 0:
            res = "竟...竟然没有3★？！"
        else:
            step = 4
            pics = []
            for i in range(0, lenth, step):
                j = min(lenth, i + step)
                pics.append(chara.gen_team_pic(res[i:j], star_slot_verbose=False))
            res = concat_pic(pics)
            res = pic2b64(res)
            res = MessageSegment.image(res)
        msg = [
            f"素敵な仲間が増えますよ！ {res}",
            f"★★★×{up+s3} ★★×{s2} ★×{s1}",
            f"获得记忆碎片×{100*up}与女神秘石×{50*(up+s3) + 10*s2 + s1}！\n第{result['first_up_pos']}抽首次获得up角色" if up else f"获得女神秘石{50*(up+s3) + 10*s2 + s1}个！"
        ]
        if up == 0 and s3 == 0:
            msg.append("太惨了，咱们还是退款删游吧...")
        elif up == 0 and s3 > 5:
            msg.append("up呢？我的up呢？")
        elif up == 0 and s3 <= 2:
            msg.append("这位酋长，梦幻包考虑一下？")
        elif up == 0:
            msg.append("据说天井的概率只有12.16%")
        elif up <= 2:
            if result['first_up_pos'] < 50:
                msg.append("你的喜悦我收到了，滚去喂鲨鱼吧！")
            elif result['first_up_pos'] < 100:
                msg.append("已经可以了，您已经很欧了")
            elif result['first_up_pos'] > 190:
                msg.append("标 准 结 局")
            elif result['first_up_pos'] > 150:
                msg.append("补井还是不补井，这是一个问题...")
            else:
                msg.append("期望之内，亚洲水平")
        elif up == 3:
            msg.append("抽井母五一气呵成！多出30等专武～")
        elif up >= 4:
            msg.append("记忆碎片一大堆！您是托吧？")
        msg = Message('\n'.join(msg))
        await gacha_200.finish(msg)


@kakin.got('ids', prompt='请at需要充值的用户，或输入对方的id', args_parser=parse_uid)
async def paywerful(bot: Bot, event: CQEvent, state: T_State):
    if event.user_id not in salmon.configs.SUPERUSERS:
        await kakin.finish('Insufficient authority.')
    if not state['ids']:
        await kakin.finish('Invalid input.')
    count = 0
    for id in state['ids']:
        jewel_limit.reset(id)
        tenjo_limit.reset(id)
        count += 1
    await kakin.finish(f"已为{count}位用户充值完毕！谢谢惠顾～")
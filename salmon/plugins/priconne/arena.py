import base64
import os
import time
import re
from PIL import Image, ImageDraw, ImageFont
from nonebot.exception import FinishedException
from nonebot.adapters.cqhttp.event import GroupMessageEvent, PrivateMessageEvent
import salmon
from salmon import aiohttpx, configs, Service, R, Bot
from salmon.typing import CQEvent, Message, MessageSegment
from salmon.util import FreqLimiter, concat_pic, pic2b64
from salmon.plugins.priconne.pcr_data import chara
try:
    import ujson as json
except:
    import json


sv_help = '''
[怎么拆] 接防守队角色名 查询竞技场解法
'''.strip()
sv = Service('pcr-arena', help_=sv_help, bundle='pcr查询')


lmt = FreqLimiter(5)

"""
Database for arena likes & dislikes
DB is a dict like: { 'md5_id': {'like': set(qq), 'dislike': set(qq)} }
"""
DB_PATH = os.path.expanduser("~/.salmon/arena_db.json")
DB = {}
try:
    with open(DB_PATH, encoding="utf8") as f:
        DB = json.load(f)
    for k in DB:
        DB[k] = {
            "like": set(DB[k].get("like", set())),
            "dislike": set(DB[k].get("dislike", set())),
        }
except FileNotFoundError:
    sv.logger.warning(f"arena_db.json not found, will create when needed.")


def dump_db():
    """
    Dump the arena databese.
    json do not accept set object, this function will help to convert.
    """
    j = {}
    for k in DB:
        j[k] = {
            "like": list(DB[k].get("like", set())),
            "dislike": list(DB[k].get("dislike", set())),
        }
    with open(DB_PATH, "w", encoding="utf8") as f:
        json.dump(j, f, ensure_ascii=False)

    
def get_likes(id_):
    return DB.get(id_, {}).get("like", set())


def add_like(id_, uid):
    e = DB.get(id_, {})
    l = e.get("like", set())
    k = e.get("dislike", set())
    l.add(uid)
    k.discard(uid)
    e["like"] = l
    e["dislike"] = k
    DB[id_] = e


def get_dislikes(id_):
    return DB.get(id_, {}).get("dislike", set())


def add_dislike(id_, uid):
    e = DB.get(id_, {})
    l = e.get("like", set())
    k = e.get("dislike", set())
    l.discard(uid)
    k.add(uid)
    e["like"] = l
    e["dislike"] = k
    DB[id_] = e


_last_query_time = 0
quick_key_dic = {}  # {quick_key: true_id}


def refresh_quick_key_dic():
    global _last_query_time
    now = time.time()
    if now - _last_query_time > 300:
        quick_key_dic.clear()
    _last_query_time = now


def gen_quick_key(true_id: str, user_id: int) -> str:
    qkey = int(true_id[-6:], 16)
    while qkey in quick_key_dic and quick_key_dic[qkey] != true_id:
        qkey = (qkey + 1) & 0xFFFFFF
    quick_key_dic[qkey] = true_id
    mask = user_id & 0xFFFFFF
    qkey ^= mask
    return base64.b32encode(qkey.to_bytes(3, "little")).decode()[:5]


def get_true_id(quick_key: str, user_id: int) -> str:
    mask = user_id & 0xFFFFFF
    if not isinstance(quick_key, str) or len(quick_key) != 5:
        return None
    qkey = (quick_key + "===").encode()
    qkey = int.from_bytes(base64.b32decode(qkey, casefold=True, map01=b"I"), "little")
    qkey ^= mask
    return quick_key_dic.get(qkey, None)


def __get_auth_key():
    return configs.priconne.arena.AUTH_KEY


async def do_query(id_list, user_id, region=1):
    id_list = [x * 100 + 1 for x in id_list]
    header = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.87 Safari/537.36",
        "authorization": __get_auth_key(),
    }
    payload = {
        "_sign": "a",
        "def": id_list,
        "nonce": "a",
        "page": 1,
        "sort": 1,
        "ts": int(time.time()),
        "region": region,
    }
    sv.logger.debug(f"Arena query {payload=}")
    try:
        resp = await aiohttpx.post(
            "https://api.pcrdfans.com/x/v1/search",
            headers=header,
            json=payload,
            timeout=10,
        )
        res = resp.json
        sv.logger.debug(f"len(res)={len(res)}")
    except Exception as e:
        sv.logger.exception(e)
        return None
    if res["code"]:
        sv.logger.error(f"Arena query failed.\nResponse={res}\nPayload={payload}")
        raise aiohttpx.HTTPError(response=res)
    result = res.get("data", {}).get("result")
    if result is None:
        return None
    ret = []
    for entry in result:
        eid = entry["id"]
        likes = get_likes(eid)
        dislikes = get_dislikes(eid)
        ret.append(
            {
                "qkey": gen_quick_key(eid, user_id),
                "atk": [
                    chara.fromid(c["id"] // 100, c["star"], c["equip"])
                    for c in entry["atk"]
                ],
                "def": [
                    chara.fromid(c["id"] // 100, c["star"], c["equip"])
                    for c in entry["def"]
                ],
                "up": entry["up"],
                "down": entry["down"],
                "my_up": len(likes),
                "my_down": len(dislikes),
                "user_like": 1
                if user_id in likes
                else -1
                if user_id in dislikes
                else 0,
            }
        )
    return ret


async def do_like(qkey, user_id, action):
    true_id = get_true_id(qkey, user_id)
    if true_id is None:
        raise KeyError
    add_like(true_id, user_id) if action > 0 else add_dislike(true_id, user_id)
    dump_db()
    # TODO: upload to website


aliases = ('怎么拆', '怎么解', '怎么打', '如何拆', '如何解', '如何打', 'jjc查询')
aliases_b = tuple('b' + a for a in aliases) + tuple('B' + a for a in aliases)
aliases_tw = tuple('台' + a for a in aliases)
aliases_jp = tuple('日' + a for a in aliases)

try:
    thumb_up_i = R.img('priconne/gadget/thumb-up-i.png').open().resize((16, 16), Image.LANCZOS)
    thumb_up_a = R.img('priconne/gadget/thumb-up-a.png').open().resize((16, 16), Image.LANCZOS)
    thumb_down_i = R.img('priconne/gadget/thumb-down-i.png').open().resize((16, 16), Image.LANCZOS)
    thumb_down_a = R.img('priconne/gadget/thumb-down-a.png').open().resize((16, 16), Image.LANCZOS)
except Exception as e:
    sv.logger.exception(e)

arena_query = sv.on_fullmatch('查竞技场', aliases=aliases, only_group=False)
arena_query_b = sv.on_fullmatch('b竞技场', aliases=aliases_b, only_group=False)
arena_query_tw = sv.on_fullmatch('台竞技场', aliases=aliases_tw, only_group=False)
arena_query_jp = sv.on_fullmatch('日竞技场', aliases=aliases_jp, only_group=False)

@arena_query.handle()
async def arena_query(bot: Bot, event: CQEvent):
    await _arena_query(bot, event, region=1)

@arena_query_b.handle()
async def arena_query(bot: Bot, event: CQEvent):
    await _arena_query(bot, event, region=2)

@arena_query_tw.handle()
async def arena_query(bot: Bot, event: CQEvent):
    await _arena_query(bot, event, region=3)

@arena_query_jp.handle()
async def arena_query(bot: Bot, event: CQEvent):
    await _arena_query(bot, event, region=4)


def render_atk_def_teams(entries, border_pix=5):
    n = len(entries)
    icon_size = 64
    im = Image.new('RGBA', (5 * icon_size + 100, n * (icon_size + border_pix) - border_pix), (255, 255, 255, 255))
    font = ImageFont.truetype('fonts/msyh.ttf', 16)
    draw = ImageDraw.Draw(im)
    for i, e in enumerate(entries):
        y1 = i * (icon_size + border_pix)
        y2 = y1 + icon_size
        for j, c in enumerate(e['atk']):
            icon = c.render_icon(icon_size)
            x1 = j * icon_size
            x2 = x1 + icon_size
            im.paste(icon, (x1, y1, x2, y2), icon)
        thumb_up = thumb_up_a if e['user_like'] > 0 else thumb_up_i
        thumb_down = thumb_down_a if e['user_like'] < 0 else thumb_down_i
        x1 = 5 * icon_size + 5
        x2 = x1 + 16
        im.paste(thumb_up, (x1, y1+22, x2, y1+38), thumb_up)
        im.paste(thumb_down, (x1, y1+44, x2, y1+60), thumb_down)
        draw.text((x1, y1), e['qkey'], (0, 0, 0, 255), font)
        draw.text((x1+16, y1+20), f"{e['up']}+{e['my_up']}" if e['my_up'] else f"{e['up']}", (0, 0, 0, 255), font)
        draw.text((x1+16, y1+40), f"{e['down']}+{e['my_down']}" if e['my_down'] else f"{e['down']}", (0, 0, 0, 255), font)
    return im


async def _arena_query(bot: Bot, event: CQEvent, region: int):
    uid = event.user_id
    if isinstance(event, PrivateMessageEvent):
        if uid not in salmon.configs.SUPERUSERS:
            await bot.send(event, '非维护组请在群聊中查询')
            raise FinishedException
    refresh_quick_key_dic()
    at_sender = Message(f'[CQ:at,qq={uid}]')
    if not lmt.check(uid):
        msg = '您查询得过于频繁，请稍等片刻'
        if isinstance(event, GroupMessageEvent):
            msg = at_sender + msg
        await bot.send(event, msg)
        raise FinishedException
    lmt.start_cd(uid)
    # 处理输入数据
    defen = event.message.extract_plain_text()
    defen = re.sub(r'[?？，,_]', '', defen)
    defen, unknown = chara.roster.parse_team(defen)
    if unknown:
        _, name, score = chara.guess_id(unknown)
        if score < 70 and not defen:
            return  # 忽略无关对话
        msg = f'无法识别"{unknown}"' if score < 70 else f'无法识别"{unknown}" 您说的有{score}%可能是{name}'
        await bot.send(event, msg)
        raise FinishedException
    if not defen:
        msg = '查询请发送"怎么拆+防守队伍"(无需+号)'
        if isinstance(event, GroupMessageEvent):
            msg = at_sender + msg
        await bot.send(event, msg)
        raise FinishedException
    if len(defen) > 5:
        msg = '编队不能多于5名角色'
        if isinstance(event, GroupMessageEvent):
            msg = at_sender + msg
        await bot.send(event, msg)
        raise FinishedException
    if len(defen) < 5:
        msg = '由于数据库限制，少于5名角色的检索条件请移步pcrdfans.com进行查询'
        if isinstance(event, GroupMessageEvent):
            msg = at_sender + msg
        await bot.send(event, msg)
        raise FinishedException
    if len(defen) != len(set(defen)):
        msg = '编队中含重复角色'
        if isinstance(event, GroupMessageEvent):
            msg = at_sender + msg
        await bot.send(event, msg)
        raise FinishedException
    if any(chara.is_npc(i) for i in defen):
        msg = '编队中含未实装角色'
        if isinstance(event, GroupMessageEvent):
            msg = at_sender + msg
        await bot.send(event, msg)
        raise FinishedException
    if 1004 in defen:
        msg = '\n⚠️您正在查询普通版炸弹人\n※万圣版可用万圣炸弹人/瓜炸等别称'
        if isinstance(event, GroupMessageEvent):
            msg = at_sender + msg
        await bot.send(event, msg)
        raise FinishedException
    # 执行查询
    sv.logger.info('Doing query...')
    res = None
    try:
        res = await do_query(defen, uid, region)
    except salmon.aiohttpx.HTTPError as e:
        code = e.response["code"]
        if code == 117:
            await bot.send(event, "高峰期服务器限流！请前往pcrdfans.com/battle查询")
        else:
            await bot.send(event, at_sender + f'CODE{code} 查询出错，请联系维护组调教\n请先前往pcrdfans.com进行查询')
        raise FinishedException
    sv.logger.info('Got response!')
    # 处理查询结果
    if res is None:
        msg = '数据库未返回数据，请再次尝试查询或前往pcrdfans.com'
        if isinstance(event, GroupMessageEvent):
            msg = at_sender + msg
        await bot.send(event, msg)
        raise FinishedException
    if not len(res):
        msg = '抱歉没有查询到解法\n※没有作业说明随便拆 发挥你的想象力～★\n作业上传请前往pcrdfans.com'
        if isinstance(event, GroupMessageEvent):
            msg = at_sender + msg
        await bot.send(event, msg)
        raise FinishedException
    res = res[:min(6, len(res))]    # 限制显示数量，截断结果
    # 发送回复
    sv.logger.info('Arena generating picture...')
    teams = render_atk_def_teams(res)
    teams = pic2b64(teams)
    teams = MessageSegment.image(teams)
    sv.logger.info('Arena picture ready!')
    # 纯文字版
    # atk_team = '\n'.join(map(lambda entry: ' '.join(map(lambda x: f"{x.name}{x.star if x.star else ''}{'专' if x.equip else ''}" , entry['atk'])) , res))
    # details = [" ".join([
    #     f"赞{e['up']}+{e['my_up']}" if e['my_up'] else f"赞{e['up']}",
    #     f"踩{e['down']}+{e['my_down']}" if e['my_down'] else f"踩{e['down']}",
    #     e['qkey'],
    #     "你赞过" if e['user_like'] > 0 else "你踩过" if e['user_like'] < 0 else ""
    # ]) for e in res]
    # defen = [ chara.fromid(x).name for x in defen ]
    # defen = f"防守方【{' '.join(defen)}】"
    at = str(MessageSegment.at(event.user_id))
    msg = [
        # defen,
        f'已为骑士{at}查询到以下进攻方案：',
        str(teams),
        # '作业评价：',
        # *details,
        # '※发送"点赞/点踩"可进行评价'
    ]
    if region == 1:
        msg.append('※使用"b怎么拆"或"台怎么拆"可按服过滤')
    msg.append('Support by pcrdfans_com')
    sv.logger.debug('Arena sending result...')
    await bot.send(event, '\n'.join(msg))
    sv.logger.debug('Arena result sent!')
    raise FinishedException
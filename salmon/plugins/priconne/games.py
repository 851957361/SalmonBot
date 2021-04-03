import os
import sqlite3
import asyncio
import random
from nonebot.adapters.cqhttp.event import GroupMessageEvent, PrivateMessageEvent
from salmon import Service, Bot, util
from salmon.typing import MessageSegment, Message, CQEvent
from salmon.plugins.priconne.pcr_data import _pcr_data, chara


PATCH_SIZE = 32
PREPARE_TIME = 5
A_TURN_TIME = 20
D_TURN_TIME = 12
TURN_NUMBER = 5
DB_PATH_AVATAR = os.path.expanduser("~/.salmon/pcr_avatar_guess.db")
DB_PATH_DESC = os.path.expanduser("~/.salmon/pcr_desc_guess.db")
BLACKLIST_ID = [1072, 1908, 4031, 9000]

sva = Service(
    "pcr-avatar-guess",
    bundle="pcr娱乐",
    help_="""
[猜头像] 猜猜bot随机发送的头像的一小部分来自哪位角色
[猜头像排行] 显示小游戏的群排行榜(只显示前十)
""".strip(),
)

svd = Service(
    "pcr-desc-guess", 
    bundle="pcr娱乐", 
    help_="""
[猜角色] 猜猜bot在描述哪位角色
[猜角色排行] 显示小游戏的群排行榜(只显示前十)
""".strip()
)

avatar_rank = sva.on_fullmatch('猜头像排行', aliases={'猜头像排名', '猜头像排行榜', '猜头像群排行'}, only_group=False)
desc_rank = svd.on_fullmatch('猜角色排行', aliases={'猜角色排名', '猜角色排行榜', '猜角色群排行'}, only_group=False)
avatar_guess = sva.on_fullmatch('猜头像', only_group=False)
desc_guess = svd.on_fullmatch('猜角色', only_group=False)


class Dao:
    def __init__(self, db_path):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._create_table()

    def connect(self):
        return sqlite3.connect(self.db_path)

    def _create_table(self):
        with self.connect() as conn:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS win_record "
                "(gid INT NOT NULL, uid INT NOT NULL, count INT NOT NULL, PRIMARY KEY(gid, uid))"
            )

    def get_win_count(self, gid, uid):
        with self.connect() as conn:
            r = conn.execute(
                "SELECT count FROM win_record WHERE gid=? AND uid=?", (gid, uid)
            ).fetchone()
            return r[0] if r else 0

    def record_winning(self, gid, uid):
        n = self.get_win_count(gid, uid)
        n += 1
        with self.connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO win_record (gid, uid, count) VALUES (?, ?, ?)",
                (gid, uid, n),
            )
        return n

    def get_ranking(self, gid):
        with self.connect() as conn:
            r = conn.execute(
                "SELECT uid, count FROM win_record WHERE gid=? ORDER BY count DESC LIMIT 10",
                (gid,),
            ).fetchall()
            return r


class GameMaster:
    def __init__(self, db_path):
        self.db_path = db_path
        self.playing = {}

    def is_playing(self, gid):
        return gid in self.playing

    def start_game(self, gid):
        return Game(gid, self)

    def get_game(self, gid):
        return self.playing[gid] if gid in self.playing else None

    @property
    def db(self):
        return Dao(self.db_path)


class Game:
    def __init__(self, gid, game_master):
        self.gid = gid
        self.gm = game_master
        self.answer = 0
        self.winner = 0

    def __enter__(self):
        self.gm.playing[self.gid] = self
        return self

    def __exit__(self, type_, value, trace):
        del self.gm.playing[self.gid]

    def record(self):
        return self.gm.db.record_winning(self.gid, self.winner)


gma = GameMaster(DB_PATH_AVATAR)
gmd = GameMaster(DB_PATH_DESC)


@avatar_rank.handle()
async def ar(bot: Bot, event: CQEvent):
    if isinstance(event, PrivateMessageEvent):
        await avatar_rank.finish('请在群聊中查看')
    elif isinstance(event, GroupMessageEvent):
        ranking = gma.db.get_ranking(event.group_id)
        msg = ["【猜头像小游戏排行榜】"]
        for i, item in enumerate(ranking):
            uid, count = item
            m = await bot.get_group_member_info(
                self_id=event.self_id, group_id=event.group_id, user_id=uid
            )
            name = str(m["card"]) or str(m["nickname"]) or str(uid)
            msg.append(f"第{i + 1}名：{name} 猜对{count}次")
        await bot.send(event, "\n".join(msg))


@desc_rank.handle()
async def dr(bot: Bot, event: CQEvent):
    if isinstance(event, PrivateMessageEvent):
        await desc_rank.finish('请在群聊中查看')
    elif isinstance(event, GroupMessageEvent):
        ranking = gmd.db.get_ranking(event.group_id)
        msg = ["【猜角色小游戏排行榜】"]
        for i, item in enumerate(ranking):
            uid, count = item
            m = await bot.get_group_member_info(
                self_id=event.self_id, group_id=event.group_id, user_id=uid
            )
            name = str(m["card"]) or str(m["nickname"]) or str(uid)
            msg.append(f"第{i + 1}名：{name} 猜对{count}次")
        await bot.send(event, "\n".join(msg))


@avatar_guess.handle()
async def ag(bot: Bot, event: CQEvent):
    if isinstance(event, PrivateMessageEvent):
        await avatar_guess.finish('本功能仅支持群聊')
    elif isinstance(event, GroupMessageEvent):
        if gma.is_playing(event.group_id):
            await avatar_guess.finish('游戏仍在进行中…')
        with gma.start_game(event.group_id) as game1:
            ids = list(_pcr_data.CHARA_NAME.keys())
            game1.answer = random.choice(ids)
            while chara.is_npc(game1.answer):
                game1.answer = random.choice(ids)
            c = chara.fromid(game1.answer)
            img = c.icon.open()
            w, h = img.size
            l = random.randint(0, w - PATCH_SIZE)
            u = random.randint(0, h - PATCH_SIZE)
            cropped = img.crop((l, u, l + PATCH_SIZE, u + PATCH_SIZE))
            cropped = MessageSegment.image(util.pic2b64(cropped))
            await bot.send(event, Message(f"猜猜这个图片是哪位角色头像的一部分?({A_TURN_TIME}s后公布答案) {cropped}"))
            await asyncio.sleep(A_TURN_TIME)
            if game1.winner:
                return
        await bot.send(event, Message(f"正确答案是：{c.name} {c.icon.cqcode}\n很遗憾，没有人答对~"))


@desc_guess.handle()
async def dg(bot: Bot, event: CQEvent):
    if isinstance(event, PrivateMessageEvent):
        await desc_guess.finish('本功能仅支持群聊')
    elif isinstance(event, GroupMessageEvent):
        if gmd.is_playing(event.group_id):
            await bot.finish(event, "游戏仍在进行中…")
        with gmd.start_game(event.group_id) as game2:
            game2.answer = random.choice(list(_pcr_data.CHARA_PROFILE.keys()))
            profile = _pcr_data.CHARA_PROFILE[game2.answer]
            kws = list(profile.keys())
            kws.remove('名字')
            random.shuffle(kws)
            kws = kws[:TURN_NUMBER]
            await bot.send(event, f"{PREPARE_TIME}秒后每隔{D_TURN_TIME}秒我会给出某位角色的一个描述，根据这些描述猜猜她是谁~")
            await asyncio.sleep(PREPARE_TIME)
            for i, k in enumerate(kws):
                await bot.send(event, f"提示{i + 1}/{len(kws)}:\n她的{k}是 {profile[k]}")
                await asyncio.sleep(D_TURN_TIME)
                if game2.winner:
                    return
            c = chara.fromid(game2.answer)
        await bot.send(event, Message(f"正确答案是：{c.name} {c.icon.cqcode}\n很遗憾，没有人答对~"))


@sva.on_message()
async def a_input_chara_name(bot: Bot, event: CQEvent):
    game1 = gma.get_game(event.group_id)
    if not game1 or game1.winner:
        return
    c = chara.fromname(event.message.extract_plain_text())
    if c.id != chara.UNKNOWN and c.id == game1.answer:
        game1.winner = event.user_id
        n = game1.record()
        msg = f"正确答案是：{c.name}{c.icon.cqcode}\n{MessageSegment.at(event.user_id)}猜对了，真厉害！TA已经猜对{n}次了~\n(此轮游戏将在几秒后自动结束，请耐心等待)"
        await bot.send(event, Message(msg))


@svd.on_message()
async def d_input_chara_name(bot: Bot, event: CQEvent):
    game2 = gmd.get_game(event.group_id)
    if not game2 or game2.winner:
        return
    c = chara.fromname(event.message.extract_plain_text())
    if c.id != chara.UNKNOWN and c.id == game2.answer:
        game2.winner = event.user_id
        n = game2.record()
        msg = f"正确答案是：{c.name}{c.icon.cqcode}\n{MessageSegment.at(event.user_id)}猜对了，真厉害！TA已经猜对{n}次了~\n(此轮游戏将在几秒后自动结束，请耐心等待)"
        await bot.send(event, Message(msg))
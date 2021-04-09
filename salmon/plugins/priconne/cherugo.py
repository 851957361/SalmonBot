"""切噜语（ちぇる語, Language Cheru）转换

定义:
    W_cheru = '切' ^ `CHERU_SET`+
    切噜词均以'切'开头，可用字符集为`CHERU_SET`

    L_cheru = {W_cheru ∪ `\\W`}*
    切噜语由切噜词与标点符号连接而成
"""

import re
from itertools import zip_longest
from salmon import Service, util, Bot
from salmon.typing import CQEvent, T_State, GroupMessageEvent, PrivateMessageEvent, Message


sv = Service('pcr-cherugo', bundle='pcr娱乐', help_='''
[切噜一下] 转换为切噜语
[切噜～♪切啰巴切拉切蹦切蹦] 切噜语翻译
'''.strip())

CHERU_SET = '切卟叮咧哔唎啪啰啵嘭噜噼巴拉蹦铃'
CHERU_DEKINAI = '切、切噜太长切不动勒切噜噜...'
CHERU_DIC = {c: i for i, c in enumerate(CHERU_SET)}
ENCODING = 'gb18030'
rex_split = re.compile(r'\b', re.U)
rex_word = re.compile(r'^\w+$', re.U)
rex_cheru_word: re.Pattern = re.compile(rf'切[{CHERU_SET}]+', re.U)


def grouper(iterable, n, fillvalue=None):
    args = [iter(iterable)] * n
    return zip_longest(*args, fillvalue=fillvalue)


def word2cheru(w: str) -> str:
    c = ['切']
    for b in w.encode(ENCODING):
        c.append(CHERU_SET[b & 0xf])
        c.append(CHERU_SET[(b >> 4) & 0xf])
    return ''.join(c)


def cheru2word(c: str) -> str:
    if not c[0] == '切' or len(c) < 2:
        return c
    b = []
    for b1, b2 in grouper(c[1:], 2, '切'):
        x = CHERU_DIC.get(b2, 0)
        x = x << 4 | CHERU_DIC.get(b1, 0)
        b.append(x)
    return bytes(b).decode(ENCODING, 'replace')


def str2cheru(s: str) -> str:
    c = []
    for w in rex_split.split(s):
        if rex_word.search(w):
            w = word2cheru(w)
        c.append(w)
    return ''.join(c)


def cheru2str(c: str) -> str:
    return rex_cheru_word.sub(lambda w: cheru2word(w.group()), c)


cherulize = sv.on_fullmatch('切噜一下', only_group=False)
decherulize = sv.on_fullmatch('切噜～♪', only_group=False)

@cherulize.handle()
async def cherulize_rec(bot: Bot, event: CQEvent, state: T_State):
    args = event.message.extract_plain_text()
    if args:
        state['kouyougo'] = args

@cherulize.got('kouyougo', prompt='请问要切噜什么呢？')
async def cheru(bot: Bot, event: CQEvent, state: T_State):
    s = state['kouyougo']
    if len(s) > 500:
        if isinstance(event, GroupMessageEvent):
            at_sender = Message(f'[CQ:at,qq={event.user_id}]')
            await cherulize.finish(at_sender + CHERU_DEKINAI)
        elif isinstance(event, PrivateMessageEvent):
            await cherulize.finish(CHERU_DEKINAI)
    await bot.send(event, '切噜～♪' + str2cheru(s))


@decherulize.handle()
async def decherulize_rec(bot: Bot, event: CQEvent, state: T_State):
    args = event.message.extract_plain_text()
    if args:
        state['cherugo'] = args

@decherulize.got('cherugo', prompt='请发送切噜语切噜噜~')
async def decheru(bot: Bot, event: CQEvent, state: T_State):
    s = state['cherugo']
    if len(s) > 1501:
        if isinstance(event, GroupMessageEvent):
            at_sender = Message(f'[CQ:at,qq={event.user_id}]')
            await cherulize.finish(at_sender + CHERU_DEKINAI)
        elif isinstance(event, PrivateMessageEvent):
            await cherulize.finish(CHERU_DEKINAI)
    if isinstance(event, GroupMessageEvent):
        at_sender = Message(f'[CQ:at,qq={event.user_id}]')
        msg = '的切噜噜是：\n' + util.filt_message(cheru2str(s))
        await bot.send(event, at_sender + msg)
    elif isinstance(event, PrivateMessageEvent):
        msg = '您的切噜噜是：\n' + util.filt_message(cheru2str(s))
        await bot.send(event, msg)
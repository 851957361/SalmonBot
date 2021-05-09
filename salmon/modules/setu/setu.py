import os
import requests
import random
from nonebot.adapters.cqhttp.exception import NetworkError
from salmon import priv, Service, R, Bot
import salmon
from salmon.util import DailyNumberLimiter, FreqLimiter
from salmon.typing import CQEvent, T_State, GroupMessageEvent, PrivateMessageEvent, Message


_max = 5
EXCEED_NOTICE = f'您今天已经冲过{_max}次了，请明早5点后再来！'
CD_NOTICE = '您冲得太快了，请稍候再冲'
_nlmt = DailyNumberLimiter(_max)
_flmt = FreqLimiter(5)

sv = Service('setu', manage_priv=priv.SUPERUSER, enable_on_default=False, visible=False)
setu_folder = R.img('setu/').path
if not setu_folder:
    os.makedirs(os.path.expanduser(setu_folder), exist_ok=True)


def setu_gener():
    while True:
        filelist = os.listdir(setu_folder)
        random.shuffle(filelist)
        for filename in filelist:
            if os.path.isfile(os.path.join(setu_folder, filename)):
                yield R.img('setu/', filename)


setu_gener = setu_gener()


def get_setu():
    return setu_gener.__next__()


async def send_a_setu(bot, event):
    pic = get_setu()
    try:
        await bot.send(event, Message(pic.cqcode))
    except:
        salmon.logger.error(f"发送图片{pic.path}失败")
        await bot.send(event, '涩图太涩，发不出去勒...')


setu = sv.on_rex(r'^[色涩瑟][图圖]|[来來发發给給][张張个個幅点點份丶](?P<keyword>.*?)[色涩瑟][图圖]$')

@setu.handle()
async def random_setu(bot: Bot, event: CQEvent, state: T_State):
    uid = event.user_id
    at_sender = Message(f'[CQ:at,qq={event.user_id}]')
    if not _nlmt.check(uid):
        if isinstance(event, GroupMessageEvent):   
            await setu.finish(at_sender + EXCEED_NOTICE)
        elif isinstance(event, PrivateMessageEvent):
            await setu.finish(EXCEED_NOTICE)
    if not _flmt.check(uid):
        if isinstance(event, GroupMessageEvent):
            await setu.finish(at_sender + CD_NOTICE)
        elif isinstance(event, PrivateMessageEvent):
            await setu.finish(CD_NOTICE)
    match = state['match']
    keyword = match.group('keyword')
    await online_setu(bot, event, keyword)


async def online_setu(bot, event, keyword):
    uid = event.user_id
    url = 'https://api.lolicon.app/setu/'
    params = salmon.configs.setu.setu_config
    if keyword != "":
        params["keyword"] = keyword
    else:
        keyword = ""
    resp = requests.get(url=url, params=params)
    status_code = resp.status_code
    if status_code != 200:
        salmon.logger.error("status_code error")
    resp_json = resp.json()
    resp_code = resp_json["code"]
    if resp_code != 0:
        if resp_code == 429:
            await bot.send(event, "API总调用额度达到上限，将随机发送本地图片")
            _flmt.start_cd(uid)
            _nlmt.increase(uid)
            await send_a_setu(bot, event)
            return
        elif resp_code == 404:
            await bot.send(event, resp_json["msg"] + "，将随机发送本地图库中的图片")
            _flmt.start_cd(uid)
            _nlmt.increase(uid)
            await send_a_setu(bot, event)
            return
        elif resp_code == 403:
            await bot.send(event, resp_json["msg"] + "，请联系维护（error code 403）")
            return
        elif resp_code == 401:
            await bot.send(event, resp_json["msg"] + "，请联系维护（error code 401）")
            return
        elif resp_code == -1:
            await bot.send(event, "API错误，请联系维护")
            return
    if uid not in salmon.configs.SUPERUSERS:
        _flmt.start_cd(uid)
        _nlmt.increase(uid)
    resp_data = resp_json["data"][0]
    img_url = resp_data["url"]
    msg = f'「{resp_data["title"]}」/「{resp_data["author"]}」\nPID:{resp_data["pid"]}\n[CQ:image,timeout=20,file={img_url}]'
    try:
        await bot.send(event, Message(msg))
    except NetworkError:
        salmon.logger.error(f"发送图片{img_url}失败: WebSocket API call timeout")
        await bot.send(event, '涩图太涩，发不出去勒...')
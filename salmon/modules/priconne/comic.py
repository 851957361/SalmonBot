import os
import re
from urllib.parse import urlparse, parse_qs
try:
    import ujson as json
except:
    import json
import salmon
from salmon import aiohttpx, R, Service, Bot, scheduler
from salmon.typing import CQEvent, T_State, FinishedException, Message, GroupMessageEvent, PrivateMessageEvent


sv_help = '''
官方四格漫画更新(日文)
[官漫132] 阅览指定话
'''.strip()
sv = Service('pcr-comic', help_=sv_help, bundle='pcr订阅')

def load_index():
    with open(R.get('img/priconne/comic/index.json').path, encoding='utf8') as f:
        return json.load(f)

def get_pic_name(id_):
    pre = 'episode_'
    end = '.png'
    return f'{pre}{id_}{end}'


comic = sv.on_fullmatch('官漫', only_group=False)

@comic.handle()
async def comic_rec(bot: Bot, event: CQEvent, state: T_State):
    user_info = await bot.get_stranger_info(user_id=event.user_id)
    nickname = user_info.get('nickname', '未知用户')
    args = event.message.extract_plain_text()
    if args:
        state['episode'] = args
    if isinstance(event, GroupMessageEvent):
        message = f'>{nickname}\n请发送漫画的集数'
    elif isinstance(event, PrivateMessageEvent):
        message = '请发送漫画的集数'
    state['prompt'] = message

@comic.got('episode', prompt='{prompt}')
async def read_comic(bot: Bot, event: CQEvent, state: T_State):
    episode = state['episode']
    user_info = await bot.get_stranger_info(user_id=event.user_id)
    nickname = user_info.get('nickname', '未知用户')
    if not re.fullmatch(r'\d{0,3}', episode):
        raise FinishedException
    episode = episode.lstrip('0')
    index = load_index()
    if episode not in index:
        if isinstance(event, GroupMessageEvent):
            await comic.finish(f'>{nickname}\n未查找到第{episode}话，敬请期待官方更新')
        elif isinstance(event, PrivateMessageEvent):
            await comic.finish(f'未查找到第{episode}话，敬请期待官方更新')
    title = index[episode]['title']
    pic = R.img('priconne/comic/', get_pic_name(episode)).cqcode
    if isinstance(event, GroupMessageEvent):
        await comic.finish(Message(f'>{nickname}\nプリンセスコネクト！Re:Dive公式4コマ\n第{episode}話 {title}\n{pic}'))
    elif isinstance(event, PrivateMessageEvent):
        await comic.finish(Message(f'プリンセスコネクト！Re:Dive公式4コマ\n第{episode}話 {title}\n{pic}'))


async def download_img(save_path, link):
    '''
    从link下载图片保存至save_path（目录+文件名）
    会覆盖原有文件，需保证目录存在
    '''
    salmon.logger.info(f'download_img from {link}')
    resp = await aiohttpx.get(link, timeout=10)
    salmon.logger.info(f'status_code={resp.status_code}')
    if 200 == resp.status_code:
        if re.search(r'image', resp.headers['content-type'], re.I):
            salmon.logger.info(f'is image, saving to {save_path}')
            with open(save_path, 'wb') as f:
                f.write(resp.content)
                salmon.logger.info('saved!')


async def download_comic(id_):
    '''
    下载指定id的官方四格漫画，同时更新漫画目录index.json
    episode_num可能会小于id
    '''
    base = 'https://comic.priconne-redive.jp/api/detail/'
    save_dir = R.img('priconne/comic/').path
    index = load_index()

    # 先从api获取detail，其中包含图片真正的链接
    salmon.logger.info(f'getting comic {id_} ...')
    url = base + id_
    salmon.logger.info(f'url={url}')
    resp = await aiohttpx.get(url)
    salmon.logger.info(f'status_code={resp.status_code}')
    if 200 != resp.status_code:
        return
    data = resp.json()
    data = data[0]
    episode = data['episode_num']
    title = data['title']
    link = data['cartoon']
    index[episode] = {'title': title, 'link': link}
    salmon.logger.info(f'episode={index[episode]}')
    # 下载图片并保存
    await download_img(os.path.join(save_dir, get_pic_name(episode)), link)
    # 保存官漫目录信息
    with open(os.path.join(save_dir, 'index.json'), 'w', encoding='utf8') as f:
        json.dump(index, f, ensure_ascii=False)


@scheduler.scheduled_job('cron', id='官漫更新', minute='*/5', second='25')
async def update_seeker():
    '''
    轮询官方四格漫画更新
    若有更新则推送至订阅群
    '''
    index_api = 'https://comic.priconne-redive.jp/api/index'
    index = load_index()
    # 获取最新漫画信息
    resp = await aiohttpx.get(index_api, timeout=10)
    data = resp.json()
    id_ = data['latest_cartoon']['id']
    episode = data['latest_cartoon']['episode_num']
    title = data['latest_cartoon']['title']
    # 检查是否已在目录中
    # 同一episode可能会被更新为另一张图片（官方修正），此时episode不变而id改变
    # 所以需要两步判断
    if episode in index:
        qs = urlparse(index[episode]['link']).query
        old_id = parse_qs(qs)['id'][0]
        if id_ == old_id:
            salmon.logger.info('未检测到官漫更新')
            return
    # 确定已有更新，下载图片
    salmon.logger.info(f'发现更新 id={id_}')
    await download_comic(id_)
    # 推送至各个订阅群
    pic = R.img('priconne/comic', get_pic_name(episode)).cqcode
    msg = Message(f'プリンセスコネクト！Re:Dive公式4コマ更新！\n第{episode}話 {title}\n{pic}')
    await sv.broadcast(msg, 'PCR官方四格', 0.5)
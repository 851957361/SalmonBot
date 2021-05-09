import abc
from dataclasses import dataclass
from bs4 import BeautifulSoup
import salmon
from salmon import aiohttpx, Service, scheduler, Bot
from salmon.typing import List, Union, CQEvent


svtw = Service('pcr-news-tw', bundle='pcr订阅', help_='台服新闻')
svbl = Service('pcr-news-bili', bundle='pcr订阅', help_='B服新闻')

@dataclass
class Item:
    idx: Union[str, int]
    content: str = ""

    def __eq__(self, other):
        return self.idx == other.idx


class BaseSpider(abc.ABC):
    url = None
    src_name = None
    idx_cache = set()
    item_cache = []

    @classmethod
    async def get_response(cls) -> aiohttpx.Response:
        resp = await aiohttpx.get(cls.url)
        resp.raise_for_status()
        return resp

    @staticmethod
    @abc.abstractmethod
    async def get_items(resp: aiohttpx.Response) -> List[Item]:
        raise NotImplementedError

    @classmethod
    async def get_update(cls) -> List[Item]:
        resp = await cls.get_response()
        items = await cls.get_items(resp)
        updates = [ i for i in items if i.idx not in cls.idx_cache ]
        if updates:
            cls.idx_cache = set(i.idx for i in items)
            cls.item_cache = items
        return updates
        
    @classmethod
    def format_items(cls, items) -> str:
        return f'{cls.src_name}新闻\n' + '\n'.join(map(lambda i: i.content, items))



class SonetSpider(BaseSpider):
    url = "http://www.princessconnect.so-net.tw/news/"
    src_name = "台服官网"

    @staticmethod
    async def get_items(resp: aiohttpx.Response):
        soup = BeautifulSoup(resp.text, 'lxml')
        return [
            Item(idx=dd.a["href"],
                 content=f"{dd.text}\n▲www.princessconnect.so-net.tw{dd.a['href']}"
            ) for dd in soup.find_all("dd")
        ]



class BiliSpider(BaseSpider):
    url = "http://api.biligame.com/news/list?gameExtensionId=267&positionId=2&pageNum=1&pageSize=7&typeId="
    src_name = "B服官网"

    @staticmethod
    async def get_items(resp: aiohttpx.Response):
        content = resp.json()
        items = [
            Item(idx=n["id"],
                 content="{title}\n▲game.bilibili.com/pcr/news.html#news_detail_id={id}".format_map(n)
            ) for n in content["data"]
        ]
        return items


async def news_poller(spider:BaseSpider, sv:Service, TAG):
    if not spider.item_cache:
        await spider.get_update()
        salmon.logger.info(f'{TAG}新闻缓存为空，已加载至最新')
        return
    news = await spider.get_update()
    if not news:
        salmon.logger.info(f'未检索到{TAG}新闻更新')
        return
    salmon.logger.info(f'检索到{len(news)}条{TAG}新闻更新！')
    await sv.broadcast(await spider.format_items(news), TAG, interval_time=0.5)


@scheduler.scheduled_job('cron', id='新闻动态', minute='*/5', jitter=20)
async def pcr_news_poller():
    await news_poller(SonetSpider, svtw, '台服官网')
    await news_poller(BiliSpider, svbl, 'B服官网')


async def send_news(bot: Bot, event: CQEvent, spider: BaseSpider, max_num=5):
    if not spider.item_cache:
        await spider.get_update()
    news = spider.item_cache
    news = news[:min(max_num, len(news))]
    await bot.send(event, spider.format_items(news))


twnews = svtw.on_fullmatch('台服新闻', aliases={'台服动态'}, only_group=False)
blnews = svbl.on_fullmatch('B服新闻', aliases={'b服新闻', 'B服动态', 'b服动态'}, only_group=False)

@twnews.handle()
async def tw_send(bot: Bot, event: CQEvent):
    await send_news(bot, event, SonetSpider)

@blnews.handle()
async def bl_send(bot: Bot, event: CQEvent):
    await send_news(bot, event, BiliSpider)
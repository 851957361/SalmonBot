import pytz
import aiohttp
from datetime import datetime
from salmon import Service, scheduler


sv = Service('hourcall', enable_on_default=False, help_='时报')
tz = pytz.timezone('Asia/Shanghai')

@scheduler.scheduled_job('cron', id='整点报时', hour='*')
async def hour_call():
    now = datetime.now(tz)
    nowtime = now.strftime("%H:%M")
    async with aiohttp.request(
        'POST',
        'https://v1.jinrishici.com/all.json'
    ) as resp:
        res = await resp.json()
        poem = res["content"]
        title = res["origin"]
        auth = res["author"]
        msg = f"现在时间: {nowtime}\n{poem}\n————{auth}『{title}』"
        await sv.broadcast(msg, 'hourcall', 0)
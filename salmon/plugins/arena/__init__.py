from PIL import Image, ImageDraw, ImageFont
import salmon
from salmon import Service, R, Bot
from salmon.typing import CQEvent
from salmon.util import FreqLimiter, concat_pic, pic2b64
from salmon.plugins.priconne.pcr_data import chara
from salmon.plugins.priconne.arena import arena


sv_help = '''
[怎么拆] 接防守队角色名 查询竞技场解法
'''.strip()
sv = Service('pcr-arena', help_=sv_help, bundle='pcr查询')

lmt = FreqLimiter(5)

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

arena_query = sv.on_fullmatch(aliases=aliases, only_group=False)
arena_query_b = sv.on_fullmatch(aliases=aliases_b, only_group=False)
arena_query_tw = sv.on_fullmatch(aliases=aliases_tw, only_group=False)
arena_query_jp = sv.on_fullmatch(aliases=aliases_jp, only_group=False)

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
    font = ImageFont.truetype('msyh.ttc', 16)
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
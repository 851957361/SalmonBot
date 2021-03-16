import random
from nonebot.adapters.cqhttp.event import GroupMessageEvent, PrivateMessageEvent
from salmon import Service, R, Bot
from salmon.typing import CQEvent, Message
from salmon.util import DailyNumberLimiter

sv = Service('每日签到', bundle='pcr娱乐', help_='[签到] 给主さま盖章章')

lmt = DailyNumberLimiter(1)
login_presents = [
    '扫荡券×5',  '卢币×1000', '普通EXP药水×5',  '宝石×50',  '玛那×3000',
    '扫荡券×10', '卢币×1500', '普通EXP药水×15', '宝石×80',  '白金转蛋券×1',
    '扫荡券×15', '卢币×2000', '上级精炼石×3',   '宝石×100', '白金转蛋券×1',
]
todo_list = [
    '找伊绪老师上课',
    '给宫子买布丁',
    '和真琴一起寻找伤害优衣的人',
    '找小雪探讨女装',
    '与吉塔一起登上骑空艇',
    '和霞一起调查伤害优衣的人',
    '和佩可小姐一起吃午饭',
    '找小小甜心玩过家家',
    '帮碧寻找新朋友',
    '去真步真步王国',
    '找镜华补习数学',
    '陪胡桃排练话剧',
    '和初音一起午睡',
    '成为露娜的朋友',
    '帮铃莓打扫咲恋育幼院',
    '和静流小姐一起做巧克力',
    '去伊丽莎白农场给栞小姐送书',
    '观看慈乐之音的演出',
    '解救挂树的群友',
    '来一发十连',
    '井一发当期的限定池',
    '给妈妈买一束康乃馨',
    '购买黄金保值',
    '竞技场背刺',
    '去赛马场赛马',
    '用决斗为海马带来笑容',
    '成为魔法少女',
    '来几局日麻'
]

login = sv.on_fullmatch('签到', aliases={'盖章', '妈', '妈?', '妈妈', '妈!', '妈！', '妈妈！'}, only_group=False)

@login.handle()
async def give_okodokai(bot: Bot, event: CQEvent):
    uid = event.user_id
    if not lmt.check(uid):
        await login.finish('明日はもう一つプレゼントをご用意してお待ちしますね')
    lmt.increase(uid)
    at_sender = Message(f'[CQ:at,qq={uid}]')
    present = random.choice(login_presents)
    todo = random.choice(todo_list)
    pic = Message(R.img("priconne/kokkoro_stamp.png").cqcode)
    if isinstance(event, GroupMessageEvent):
        msg = at_sender + '\nおかえりなさいませ、主さま' + pic + f'\n{present}を獲得しました\n私からのプレゼントです\n主人今天要{todo}吗？'
    elif isinstance(event, PrivateMessageEvent):
        msg = 'おかえりなさいませ、主さま' + pic + f'\n{present}を獲得しました\n私からのプレゼントです\n主人今天要{todo}吗？'
    await login.finish(msg)
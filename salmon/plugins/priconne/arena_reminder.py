from salmon import Service, scheduler


svtw = Service('pcr-arena-reminder-tw', enable_on_default=False, help_='背刺时间提醒(台B)', bundle='pcr订阅')
svjp = Service('pcr-arena-reminder-jp', enable_on_default=False, help_='背刺时间提醒(日)', bundle='pcr订阅')
msg = '骑士君、准备好背刺了吗？'

@scheduler.scheduled_job('cron', id='背刺提醒(台B)', hour='14', minute='45', jitter=20)
async def pcr_reminder_tw():
    await svtw.broadcast(msg, 'pcr-reminder-tw', 0.2)

@scheduler.scheduled_job('cron', id='背刺提醒(日)', hour='13', minute='45', jitter=20)
async def pcr_reminder_jp():
    await svjp.broadcast(msg, 'pcr-reminder-jp', 0.2)
import pytz
from functools import wraps
from typing import Callable, Any
from nonebot_plugin_apscheduler import scheduler


def scheduled_job(self, *args, **kwargs) -> Callable:
    kwargs.setdefault('timezone', pytz.timezone('Asia/Shanghai'))
    kwargs.setdefault('misfire_grace_time', 60)
    kwargs.setdefault('coalesce', True)
    def deco(func: Callable[[], Any]) -> Callable:
        @wraps(func)
        async def wrapper():
            try:
                self.logger.info(f'Scheduled job {func.__name__} start.')
                ret = await func()
                self.logger.info(f'Scheduled job {func.__name__} completed.')
                return ret
            except Exception as e:
                self.logger.error(f'{type(e)} occured when doing scheduled job {func.__name__}.')
                self.logger.exception(e)
        return scheduler.scheduled_job(*args, **kwargs)(wrapper)
    return deco
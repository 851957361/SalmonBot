from functools import wraps
from typing import Callable, Any, Awaitable
from nonebot_plugin_apscheduler import scheduler
from salmon import log


def scheduled_job(trigger: str, **kwargs) -> Callable:
    def deco(func: Callable[[], Any]) -> Callable[[], Awaitable[Any]]:
        id = kwargs.get('id', func.__name__)
        kwargs['id'] = id
        def wrapper(func: Callable[[], Any], id: str) -> Callable[[], Awaitable[Any]]:
            @wraps(func)
            async def wrapper() -> Awaitable[Any]:
                try:
                    log.logger.info(f'Scheduled job {func.__name__} start.')
                    ret = await func()
                    log.logger.info(f'Scheduled job {func.__name__} completed.')
                    return ret
                except Exception as e:
                    log.logger.error(f'{type(e)} occured when doing scheduled job {func.__name__}.')
                    log.logger.exception(e)
            return wrapper
        return scheduler.scheduled_job(trigger, **kwargs)(wrapper(func, id))
    return deco
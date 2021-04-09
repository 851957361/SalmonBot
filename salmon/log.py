from nonebot.log import logger, Filter
import os
import sys
from . import configs


class wrap_logger:
    def __init__(self, name: str) -> None:
        self.name = name

    def exception(self, message: str, exception=True):
        return logger.opt(colors=True, exception=exception).exception(
            f"<r><ly>{self.name}</> | {message}</>")

    def error(self, message: str, exception=True):
        return logger.opt(colors=True, exception=exception).error(
            f"<r><ly>{self.name}</> | {message}</>")

    def critical(self, message: str):
        return logger.opt(colors=True).critical(
            f"<ly>{self.name}</> | {message}")

    def warning(self, message: str):
        return logger.opt(colors=True).warning(
            f"<ly>{self.name}</> | {message}")

    def success(self, message: str):
        return logger.opt(colors=True).success(
            f"<ly>{self.name}</> | {message}")

    def info(self, message: str):
        return logger.opt(colors=True).info(
            f"<ly>{self.name}</> | {message}")

    def debug(self, message: str):
        return logger.opt(colors=True).debug(
            f"<ly>{self.name}</> | {message}")


root = './log'
os.makedirs(root, exist_ok=True)
_log_file = os.path.expanduser('./log/salmon.log')
_error_log_file = os.path.expanduser('./log/error.log')
_critical_log_file = os.path.expanduser('./log/critical.log')
bot_filter = Filter()
if configs.DEBUG:
    bot_filter.level = 'DEBUG'
else:
    bot_filter.level = 'INFO'
log_format = (
    "<g>{time:MM-DD HH:mm:ss}</g> "
    "[<lvl>{level}</lvl>] "
    "<c><u>{name}</u></c> | "
    "{message}")
logger.remove()
logger.add(sys.stdout,
           colorize=True,
           diagnose=False,
           filter=bot_filter,
           format=log_format)
logger.add(_log_file, rotation='05:00', retention='3 days', level='INFO', encoding='utf-8')
logger.add(_error_log_file, rotation='05:00', retention='7 days', level='ERROR', encoding='utf-8')
logger.add(_critical_log_file, rotation='05:00', retention='10 days', level='CRITICAL', encoding='utf-8')
'''
触发器的处理参考了[Akiraxie](http://github.com/AkiraXie/)的项目[hoshino.nb2](https://github.com/AkiraXie/hoshino.nb2)

Thanks to @Akiraxie dalao！
'''
import os
import re
import asyncio
from functools import wraps
from collections import defaultdict
from loguru import logger
from apscheduler import job
from nonebot_plugin_apscheduler import scheduler
from nonebot.adapters.cqhttp.utils import escape
from nonebot.adapters.cqhttp.message import MessageSegment, Message
from nonebot.matcher import Matcher, matchers, current_bot, current_event
from nonebot.rule import ArgumentParser, Rule, to_me
from nonebot.typing import T_State, T_ArgsParser, T_Handler
from nonebot.plugin import on_command, on_message, on_startswith, on_endswith, on_notice, on_request, on_shell_command
from nonebot.exception import FinishedException, PausedException, RejectedException
from nonebot.message import run_preprocessor, run_postprocessor
import salmon
from salmon.typing import *
from salmon.util import normalize_str
from salmon import log, priv, Bot
try:
    import ujson as json
except:
    import json

# service management
_loaded_services: Dict[str, "Service"] = {}  # {name: service}
_loaded_matchers: Dict["Type[Matcher]", "matcher_wrapper"] = {}
_service_bundle: Dict[str, List["Service"]] = defaultdict(list)
_service_info: Dict[str, List["Service"]] = defaultdict(list)
_re_illegal_char = re.compile(r'[\\/:*?"<>|\.]')
_service_config_dir = os.path.expanduser('~/.hoshino/service_config/')
os.makedirs(_service_config_dir, exist_ok=True)


def get_matchers() -> list:
    return matchers.items()


def keyword(*keywords: str, normal: bool = True) -> Rule:
    async def _keyword(bot: Bot, event: CQEvent, state: T_State) -> bool:
        if event.get_type() != "message":
            return False
        text = event.get_plaintext()
        if normal:
            text = normalize_str(text)
        return bool(text and any(keyword in text for keyword in keywords))

    return Rule(_keyword)


def regex(regex: str, flags: Union[int, re.RegexFlag] = 0, normal: bool = True) -> Rule:
    pattern = re.compile(regex, flags)
    async def _regex(bot: Bot, event: CQEvent, state: T_State) -> bool:
        if event.get_type() != "message":
            return False
        text = str(event.get_message())
        if normal:
            text = normalize_str(text)
        matched = pattern.search(text)
        if matched:
            state['match'] = matched
            state["_matched"] = matched.group()
            state["_matched_groups"] = matched.groups()
            state["_matched_dict"] = matched.groupdict()
            return True
        else:
            return False
    return Rule(_regex)


def wrapper(func: Callable[[], Any], id: str) -> Callable[[], Awaitable[Any]]:
    @wraps(func)
    async def _wrapper() -> Awaitable[Any]:
        try:
            logger.opt(colors=True).info(
                f'<ly>Scheduled job <c>{id}</c> started.</ly>')
            res = await func()
            logger.opt(colors=True).info(
                f'<ly>Scheduled job <c>{id}</c> completed.</ly>')
            return res
        except Exception as e:
            logger.opt(colors=True, exception=e).error(
                f'<r><bg #f8bbd0>Scheduled job <c>{id}</c> failed.</bg #f8bbd0></r>')
    return _wrapper


def _load_service_config(service_name):
    config_file = os.path.join(_service_config_dir, f'{service_name}.json')
    if not os.path.exists(config_file):
        return {}  # config file not found, return default config.
    try:
        with open(config_file, encoding='utf8') as f:
            config = json.load(f)
            return config
    except Exception as e:
        salmon.logger.exception(e)
        return {}


def _save_service_config(service):
    config_file = os.path.join(_service_config_dir, f'{service.name}.json')
    with open(config_file, 'w', encoding='utf8') as f:
        json.dump(
            {
                "name": service.name,
                "use_priv": service.use_priv,
                "manage_priv": service.manage_priv,
                "enable_on_default": service.enable_on_default,
                "visible": service.visible,
                "enable_group": list(service.enable_group),
                "disable_group": list(service.disable_group)
            },
            f,
            ensure_ascii=False,
            indent=2)


class ServiceFunc:
    def __init__(self, sv: "Service", func: Callable, only_to_me: bool, normalize_text: bool=False):
        self.sv = sv
        self.func = func
        self.only_to_me = only_to_me
        self.normalize_text = normalize_text
        self.__name__ = func.__name__

    def __call__(self, *args, **kwargs):
        return self.func(*args, **kwargs)


class Service:
    def __init__(self, name, use_priv=None, manage_priv=None, enable_on_default=None, visible=None,
                 help_=None, bundle=None):
        assert not _re_illegal_char.search(
            name), r'Service name cannot contain character in `\/:*?"<>|.`'
        config = _load_service_config(name)
        self.name = name
        self.use_priv = config.get('use_priv') or use_priv or priv.NORMAL
        self.manage_priv = config.get(
            'manage_priv') or manage_priv or priv.ADMIN
        self.enable_on_default = config.get('enable_on_default')
        if self.enable_on_default is None:
            self.enable_on_default = enable_on_default
        if self.enable_on_default is None:
            self.enable_on_default = True
        self.visible = config.get('visible')
        if self.visible is None:
            self.visible = visible
        if self.visible is None:
            self.visible = True
        self.help = help_
        self.enable_group = set(config.get('enable_group', []))
        self.disable_group = set(config.get('disable_group', []))
        self.logger = log.new_logger(name, salmon.config.DEBUG)
        self.matchers = []
        assert self.name not in _loaded_services, f'Service name "{self.name}" already exist!'
        _loaded_services[self.name] = self
        _service_info[name].append(self)
        _service_bundle[bundle or "通用"].append(self)

    @property
    def bot(self):
        return salmon.get_bot()

    @staticmethod
    def get_loaded_services() -> Dict[str, "Service"]:
        return _loaded_services

    @staticmethod
    def get_bundles():
        return _service_bundle

    @staticmethod
    def get_help():
        return _service_info

    def set_enable(self, group_id):
        self.enable_group.add(group_id)
        self.disable_group.discard(group_id)
        _save_service_config(self)
        self.logger.info(f'Service {self.name} is enabled at group {group_id}')

    def set_disable(self, group_id):
        self.enable_group.discard(group_id)
        self.disable_group.add(group_id)
        _save_service_config(self)
        self.logger.info(
            f'Service {self.name} is disabled at group {group_id}')

    def check_enabled(self, group_id):
        return bool( (group_id in self.enable_group) or (self.enable_on_default and group_id not in self.disable_group))

    def _check_all(self, ev: CQEvent):
        gid = ev.group_id
        return self.check_enabled(gid) and not priv.check_block_group(gid) and priv.check_priv(ev, self.use_priv)

    def check_service(self, only_to_me: bool = False, only_group: bool = True) -> Rule:
        async def _cs(bot: Bot, event: CQEvent, state: T_State) -> bool:
            if not 'group_id' in event.__dict__:
                return not only_group
            else:
                group_id = event.group_id
                return self.check_enabled(group_id)
        rule = Rule(_cs)
        if only_to_me:
            rule = rule & (to_me())
        return rule

    async def get_enable_groups(self) -> Dict[int, List[Bot]]:
        gl = defaultdict(list)
        for bot in salmon.get_bot_list():
            sgl = set(g['group_id'] for g in await bot.get_group_list())
            if self.enable_on_default:
                sgl = sgl - self.disable_group
            else:
                sgl = sgl & self.enable_group
            for g in sgl:
                gl[g].append(bot)
        return gl


    def on_message(self,  only_to_me: bool = False, only_group: bool = True, **kwargs) -> "matcher_wrapper":
        rule = self.check_service(only_to_me, only_group)
        kwargs['rule'] = rule
        priority = kwargs.get('priority', 1)
        mw = matcher_wrapper(self,
                             'Message.message', priority, only_group=only_group)
        self.matchers.append(str(mw))
        mw.load_matcher(on_message(**kwargs))
        _loaded_matchers[mw.matcher] = mw
        return mw


    def on_prefix(self, msg: str, only_to_me: bool = False, only_group: bool = True, **kwargs) -> "matcher_wrapper":
        rule = self.check_service(only_to_me, only_group)
        kwargs['rule'] = rule
        priority = kwargs.get('priority', 1)
        mw = matcher_wrapper(self,
                             'Message.startswith', priority, startswith=msg, only_group=only_group)
        mw.load_matcher(on_startswith(msg, **kwargs))
        self.matchers.append(str(mw))
        _loaded_matchers[mw.matcher] = mw
        return mw

        
    def on_fullmatch(self, name: str, only_to_me: bool = False, aliases: Optional[Iterable] = None, only_group: bool = True, **kwargs) -> "matcher_wrapper":
        if isinstance(aliases, str):
            aliases = set([aliases])
        elif not isinstance(aliases, set):
            if aliases:
                aliases = set([aliases]) if len(aliases) == 1 and isinstance(
                    aliases, tuple) else set(aliases)
            else:
                aliases = set()
        kwargs['aliases'] = aliases
        rule = self.check_service(only_to_me, only_group)
        kwargs['rule'] = rule
        priority = kwargs.get('priority', 1)
        mw = matcher_wrapper(self,
                             'Message.command', priority, command=name, only_group=only_group)
        matcher = on_command(name, **kwargs)
        mw.load_matcher(matcher)
        self.matchers.append(str(mw))
        _loaded_matchers[mw.matcher] = mw
        return mw


    def on_suffix(self, msg: str, only_to_me: bool = False, only_group: bool = True, **kwargs) -> "matcher_wrapper":
        rule = self.check_service(only_to_me, only_group)
        kwargs['rule'] = rule
        priority = kwargs.get('priority', 1)
        mw = matcher_wrapper(self,
                             'Message.endswith', priority, endswith=msg, only_group=only_group)
        mw.load_matcher(on_endswith(msg, **kwargs))
        self.matchers.append(str(mw))
        _loaded_matchers[mw.matcher] = mw
        return mw


    def on_keyword(self, keywords: Iterable, normal: bool = True, only_to_me: bool = False, only_group: bool = True, **kwargs) -> "matcher_wrapper":
        if isinstance(keywords, str):
            keywords = set([keywords])
        elif not isinstance(keywords, set):
            if keywords:
                keywords = set([keywords]) if len(
                    keywords) == 1 and isinstance(keywords, tuple) else set(keywords)
            else:
                keywords = set()
        rule = self.check_service(only_to_me, only_group)
        kwargs['rule'] = keyword(*keywords, normal) & rule
        priority = kwargs.get('priority', 1)
        mw = matcher_wrapper(self,
                             'Message.keyword', priority, keywords=str(keywords), only_group=only_group)
        mw.load_matcher(on_message(**kwargs))
        self.matchers.append(str(mw))
        _loaded_matchers[mw.matcher] = mw
        return mw


    def on_rex(self, pattern: str, flags: Union[int, re.RegexFlag] = 0, normal: bool = True, only_to_me: bool = False, only_group: bool = True, **kwargs) -> "matcher_wrapper":
        '''
        根据正则表达式进行匹配。
        可以通过 ``state["_matched"]`` 获取正则表达式匹配成功的文本。
        可以通过 ``state["match"]`` 获取正则表达式匹配成功后的`match`
        '''
        rule = self.check_service(only_to_me, only_group)
        rule = regex(pattern, flags, normal) & rule
        priority = kwargs.get('priority', 1)
        mw = matcher_wrapper(self,
                             'Message.regex', priority, pattern=str(pattern), flags=str(flags), only_group=only_group)
        self.matchers.append(str(mw))
        mw.load_matcher(on_message(rule, **kwargs))
        _loaded_matchers[mw.matcher] = mw
        return mw


    def on_shell_command(self, name: str, only_to_me: bool = False, aliases: Optional[Iterable] = None, parser: Optional[ArgumentParser] = None, only_group: bool = True, **kwargs) -> "matcher_wrapper":
        if isinstance(aliases, str):
            aliases = set([aliases])
        elif not isinstance(aliases, set):
            if aliases:
                aliases = set([aliases]) if len(aliases) == 1 and isinstance(
                    aliases, tuple) else set(aliases)
            else:
                aliases = set()
        kwargs['parser'] = parser
        kwargs['aliases'] = aliases
        rule = self.check_service(only_to_me, only_group)
        kwargs['rule'] = rule
        priority = kwargs.get('priority', 1)
        mw = matcher_wrapper(self,
                             'Message.shell_command', priority, command=name, only_group=only_group)
        mw.load_matcher(on_shell_command(name, **kwargs))
        self.matchers.append(str(mw))
        _loaded_matchers[mw.matcher] = mw
        return mw


    def scheduled_job(trigger: str, **kwargs):
        def deco(func: Callable[[], Any]) -> Callable[[], Awaitable[Any]]:
            id = kwargs.get('id', func.__name__)
            kwargs['id'] = id
            return scheduler.scheduled_job(trigger, **kwargs)(wrapper(func, id))
        return deco


    def add_job(func: Callable[[], Any], trigger: str, **kwargs)->job.Job:
        id = kwargs.get('id', func.__name__)
        kwargs['id'] = id
        return scheduler.add_job(wrapper(func, id), trigger, **kwargs)


    def on_notice(self,  only_group: bool = True, **kwargs) -> "matcher_wrapper":
        rule = self.check_service(0, only_group)
        priority = kwargs.get('priority', 1)
        mw = matcher_wrapper(self,
                             'Notice', priority, only_group=only_group)
        self.matchers.append(str(mw))
        mw.load_matcher(on_notice(rule, **kwargs))
        _loaded_matchers[mw.matcher] = mw
        return mw


    def on_request(self, only_group: bool = True, **kwargs) -> "matcher_wrapper":
        rule = self.check_service(0, only_group)
        priority = kwargs.get('priority', 1)
        mw = matcher_wrapper(self,
                             'Request', priority, only_group=only_group)
        self.matchers.append(str(mw))
        mw.load_matcher(on_request(rule, **kwargs))
        _loaded_matchers[mw.matcher] = mw
        return mw


    async def broadcast(self, msgs: Optional[Iterable], tag='', interval_time=0.5):
        if isinstance(msgs, (str, Message, MessageSegment)):
            msgs = (msgs,)
        gdict = await self.get_enable_groups()
        for gid in gdict.keys():
            for bot in gdict[gid]:
                sid = int(bot.self_id)
                for msg in msgs:
                    await asyncio.sleep(interval_time)
                    try:
                        await bot.send_group_msg(self_id=sid, group_id=gid, message=msg)
                        self.logger.info(
                            f"{sid}在群{gid}投递{tag}成功")
                    except:
                        self.logger.error(f'{sid}在群{gid}投递{tag}失败')


class matcher_wrapper:
    def __init__(self, sv: Service, type: str, priority: int, **info) -> None:
        self.sv = sv
        self.priority = priority
        self.info = info
        self.type = type

    def load_matcher(self, matcher: Type[Matcher]):
        self.matcher = matcher

    @staticmethod
    def get_loaded_matchers() -> List[str]:
        return list(map(str, _loaded_matchers.values()))

    def handle(self):
        def deco(func: T_Handler):
            return self.matcher.handle()(func)
        return deco

    def __call__(self, func: T_Handler) -> T_Handler:
        return self.handle()(func)

    def receive(self):
        def deco(func: T_Handler):
            return self.matcher.receive()(func)
        return deco

    def got(self,
            key: str,
            prompt: Optional[Union[str, "Message", "MessageSegment"]] = None,
            args_parser: Optional[T_ArgsParser] = None):
        def deco(func: T_Handler):
            return self.matcher.got(key, prompt, args_parser)(func)
        return deco

    async def reject(self,
                     prompt: Optional[Union[str, "Message",
                                            "MessageSegment"]] = None,
                     *,
                     call_header: bool = False,
                     at_sender: bool = False,
                     **kwargs):
        if prompt:
            await self.send(prompt, call_header=call_header, at_sender=at_sender, **kwargs)
        raise RejectedException

    async def pause(self,
                    prompt: Optional[Union[str, "Message",
                                           "MessageSegment"]] = None,
                    *,
                    call_header: bool = False,
                    at_sender: bool = False,
                    **kwargs):
        if prompt:
            await self.send(prompt, call_header=call_header, at_sender=at_sender, **kwargs)
        raise PausedException

    async def send(self, message: Union[str, "Message", "MessageSegment"],
                   *,
                   call_header: bool = False,
                   at_sender: bool = False,
                   **kwargs):
        bot = current_bot.get()
        event = current_event.get()
        if "group_id" not in event.__dict__ or not call_header:
            return await bot.send(event, message, at_sender=at_sender, **kwargs)
        if event.user_id == 80000000:
            header = '>???\n'
        else:
            info = await bot.get_group_member_info(
                group_id=event.group_id,
                user_id=event.user_id,
                no_cache=True
            )
            nickname = escape(
                info['title'] if info['title'] else info['card'] if info['card'] else info['nickname']
            )
            header = f'>{nickname}\n'
        return await bot.send(event, header+message, at_sender=at_sender, **kwargs)

    async def finish(self,
                     message: Optional[Union[str, "Message",
                                             "MessageSegment"]
                                       ] = None,
                     *,
                     call_header: bool = False,
                     at_sender: bool = False,
                     **kwargs):
        if message:
            await self.send(message, call_header=call_header, at_sender=at_sender, **kwargs)
        raise FinishedException

    def __str__(self) -> str:
        finfo = [f"{k}={v}" for k, v in self.info.items()]
        return (f"<Matcher from Sevice {self.sv.name}, priority={self.priority}, type={self.type}, "
                + ", ".join(finfo)+">")

    def __repr__(self) -> str:
        return self.__str__


@run_preprocessor
async def _(matcher: Matcher, bot: Bot, event: CQEvent, state: T_State):
    mw = _loaded_matchers.get(matcher.__class__, None)
    if mw:
        mw.sv.logger.info(f'Event will be handled by <lc>{mw}</>')


@run_postprocessor
async def _(matcher: Matcher, exception: Exception, bot: Bot, event: CQEvent, state: T_State):
    mw = _loaded_matchers.get(matcher.__class__, None)
    if mw:
        if exception:
            mw.sv.logger.error(
                f'Event handling failed from <lc>{mw}</>', False)
        mw.sv.logger.info(f'Event handling completed from <lc>{mw}</>')
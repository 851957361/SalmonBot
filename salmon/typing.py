from typing import (Any, Callable, Dict, Iterable, List, NamedTuple, Optional,
                    Set, Tuple, Union, Type, Awaitable)
from nonebot.typing import T_State, T_Handler, T_ArgsParser
from nonebot.exception import FinishedException
from nonebot.adapters.cqhttp import Event as CQEvent
from nonebot.adapters.cqhttp.message import MessageSegment, Message
from nonebot.adapters.cqhttp.event import GroupMessageEvent, PrivateMessageEvent
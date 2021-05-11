'''
From [nonebot_plugin_translator](https://github.com/Lancercmd/nonebot_plugin_translator) by @Lancercmd

Thanks to @Lancercmd dalao!

'''
import random
import string
from copy import deepcopy
from hashlib import md5
from time import time
from urllib.parse import quote_plus
import aiohttp
import salmon
from salmon import Bot, Service
from salmon.typing import CQEvent, MessageEvent, ActionFailed, T_State, GroupMessageEvent, PrivateMessageEvent
try:
    import ujson as json
except ImportError:
    import json


TXT = '''
[翻译] 机器翻译
'''.strip()

sv = Service('机器翻译', bundle='查询', help_=TXT)

app_id = salmon.configs.translate.tencent_app_id
app_key = salmon.configs.translate.tencent_app_key


def loadsJson(dict: str) -> dict:
    return json.loads(dict)


translate = sv.on_fullmatch('翻译', aliases={'机翻'}, only_group=False)


async def getReqSign(params: dict) -> str:
    keys = []
    for key in sorted(params):
        keys.append(f'{key}={quote_plus(params[key])}')
    hashed_str = f'{"&".join(keys)}&app_key={app_key}'
    sign = md5(hashed_str.encode())
    return sign.hexdigest().upper()


async def rand_string(n=8) -> str:
    return ''.join(
        random.choice(string.ascii_uppercase + string.digits)
        for _ in range(n)
    )


@translate.handle()
async def _(bot: Bot, event: CQEvent, state: T_State):
    if isinstance(event, MessageEvent):
        user_info = await bot.get_stranger_info(user_id=event.user_id)
        nickname = user_info.get('nickname', '未知用户')
        available = [
            'zh', 'en', 'fr', 'es', 'it',
            'de', 'tr', 'ru', 'pt', 'vi',
            'id', 'ms', 'th', 'jp', 'kr'
        ]
        state['available'] = ' | '.join(available)
        state['valid'] = deepcopy(available)
        if event.get_plaintext():
            for language in available:
                if event.get_plaintext().startswith(language):
                    state['source'] = language
                    break
            if 'source' in state:
                input = event.get_plaintext().split(' ', 2)
                if state['source'] == 'zh':
                    available.remove('zh')
                elif state['source'] == 'en':
                    for i in ['jp', 'kr']:
                        available.remove(i)
                    available.remove(state['source'])
                elif state['source'] in ['fr', 'es', 'it', 'de', 'tr', 'ru', 'pt']:
                    for i in ['vi', 'id', 'ms', 'th', 'jp', 'kr']:
                        available.remove(i)
                    available.remove(state['source'])
                elif state['source'] in ['vi', 'id', 'ms', 'th']:
                    available = ['zh', 'en']
                else:
                    available = ['zh']
                if len(available) == 1:
                    state['target'] = 'zh'
                    salmon.logger.info(input)
                    if len(input) == 3:
                        state['text'] = input[2]
                    else:
                        state['text'] = input[1]
                elif len(input) == 3:
                    state['target'] = input[1]
                    state['text'] = input[2]
                elif len(input) == 2:
                    for language in available:
                        if input[0] in available:
                            state['target'] = input[1]
                        else:
                            state['text'] = input[1]
            else:
                state['text'] = event.get_plaintext()
        if isinstance(event, GroupMessageEvent):
            message = f'>{nickname}\n请选择输入语种，可选值如下~\n{state["available"]}'
        elif isinstance(event, PrivateMessageEvent):
            message = f'请选择输入语种，可选值如下~\n{state["available"]}'
        state['prompt'] = message
    else:
        salmon.logger.warning('Not supported: translator')
        return


@translate.got('source', prompt='{prompt}')
async def _(bot: Bot, event: CQEvent, state: T_State):
    if isinstance(event, MessageEvent):
        user_info = await bot.get_stranger_info(user_id=event.user_id)
        nickname = user_info.get('nickname', '未知用户')
        available = deepcopy(state['valid'])
        if not state['source'] in state['valid']:
            if isinstance(event, GroupMessageEvent):
                message = f'>{nickname}\n不支持的输入语种 {state["source"]}'
            elif isinstance(event, PrivateMessageEvent):
                message = f'不支持的输入语种 {state["source"]}'
            try:
                await translate.finish(message)
            except ActionFailed as e:
                salmon.logger.error(
                    f'ActionFailed | {e.info["msg"].lower()} | retcode = {e.info["retcode"]} | {e.info["wording"]}'
                )
                return
        elif state['source'] == 'zh':
            available.remove('zh')
        elif state['source'] == 'en':
            for i in ['jp', 'kr']:
                available.remove(i)
            available.remove(state['source'])
        elif state['source'] in ['fr', 'es', 'it', 'de', 'tr', 'ru', 'pt']:
            for i in ['vi', 'id', 'ms', 'th', 'jp', 'kr']:
                available.remove(i)
            available.remove(state['source'])
        elif state['source'] in ['vi', 'id', 'ms', 'th']:
            available = ['zh', 'en']
        else:
            available = ['zh']
        if len(available) == 1:
            state['target'] = 'zh'
        else:
            state['available'] = ' | '.join(available)
            state['valid'] = deepcopy(available)
        if isinstance(event, GroupMessageEvent):
            message = f'>{nickname}\n请选择目标语种，可选值如下~\n{state["available"]}'
        elif isinstance(event, PrivateMessageEvent):
            message = f'请选择目标语种，可选值如下~\n{state["available"]}'
        state['prompt'] = message
    else:
        salmon.logger.warning('Not supported: translator')
        return


@translate.got('target', prompt='{prompt}')
async def _(bot: Bot, event: CQEvent, state: T_State):
    if isinstance(event, MessageEvent):
        user_info = await bot.get_stranger_info(user_id=event.user_id)
        nickname = user_info.get('nickname', '未知用户')
        if not state['target'] in state['valid']:
            if isinstance(event, GroupMessageEvent):
                message = f'>{nickname}\n不支持的目标语种 {state["target"]}'
            elif isinstance(event, PrivateMessageEvent):
                message = f'不支持的目标语种 {state["target"]}'
            try:
                await translate.finish(message)
            except ActionFailed as e:
                salmon.logger.error(
                    f'ActionFailed | {e.info["msg"].lower()} | retcode = {e.info["retcode"]} | {e.info["wording"]}'
                )
                return
        if isinstance(event, GroupMessageEvent):
            message = f'>{nickname}\n请输入要翻译的内容~'
        elif isinstance(event, PrivateMessageEvent):
            message = '请输入要翻译的内容~'
        state['prompt'] = message
    else:
        salmon.logger.warning('Not supported: translator')
        return


@translate.got('text', prompt='{prompt}')
async def _(bot: Bot, event: CQEvent, state: T_State):
    if isinstance(event, MessageEvent):
        user_info = await bot.get_stranger_info(user_id=event.user_id)
        nickname = user_info.get('nickname', '未知用户')
        param = {
            'app_id': f'{app_id}',
            'time_stamp': f'{int(time())}',
            'nonce_str': await rand_string(),
            'text': state['text'],
            'source': state['source'],
            'target': state['target']
        }
        param['sign'] = await getReqSign(param)
        async with aiohttp.request(
            'POST',
            'https://api.ai.qq.com/fcgi-bin/nlp/nlp_texttranslate',
            params=param
        ) as resp:
            code = resp.status
            if code != 200:
                message = '※ 网络异常，请稍后再试~'      
                try:
                    await translate.finish(message)
                except ActionFailed as e:
                    salmon.logger.error(
                        f'ActionFailed | {e.info["msg"].lower()} | retcode = {e.info["retcode"]} | {e.info["wording"]}'
                    )
                    return
            data = loadsJson(await resp.read())
        if data['ret']:
            if isinstance(event, GroupMessageEvent):
                message = f'>{nickname}\n※ 翻译失败，请简化文本~'
            elif isinstance(event, PrivateMessageEvent):
                message = '※ 翻译失败，请简化文本~'
            try:
                await translate.finish(message)
            except ActionFailed as e:
                salmon.logger.error(
                    f'ActionFailed | {e.info["msg"].lower()} | retcode = {e.info["retcode"]} | {e.info["wording"]}'
                )
                return
        message = data['data']['target_text']
        try:
            if isinstance(event, GroupMessageEvent):
                sender = f'>{nickname}\n'
                await translate.finish(sender + message)
            elif isinstance(event, PrivateMessageEvent):   
                await translate.finish(message)
        except ActionFailed as e:
            salmon.logger.error(
                f'ActionFailed | {e.info["msg"].lower()} | retcode = {e.info["retcode"]} | {e.info["wording"]}'
            )
            return
    else:
        salmon.logger.warning('Not supported: translator')
        return
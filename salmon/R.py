import os
from urllib.parse import urljoin
from urllib.request import pathname2url

from nonebot.adapters.cqhttp.message import MessageSegment
from PIL import Image

import salmon
from salmon import logger, util

class ResObj:
    def __init__(self, res_path):
        res_dir = os.path.expanduser(salmon.configs.RES_DIR)
        fullpath = os.path.abspath(os.path.join(res_dir, res_path))
        if not fullpath.startswith(os.path.abspath(res_dir)):
            raise ValueError('Cannot access outside RESOUCE_DIR')
        self.__path = os.path.normpath(res_path)

    @property
    def url(self):
        """资源文件的url，供酷Q（或其他远程服务）使用"""
        return urljoin(salmon.configs.RES_URL, pathname2url(self.__path))

    @property
    def path(self):
        """资源文件的路径，供bot内部使用"""
        return os.path.join(salmon.configs.RES_DIR, self.__path)

    @property
    def exist(self):
        return os.path.exists(self.path)


class ResImg(ResObj):
    @property
    def cqcode(self) -> MessageSegment:
        if salmon.configs.RES_PROTOCOL == 'http':
            return MessageSegment.image(self.url)
        elif salmon.configs.RES_PROTOCOL == 'file':
            return MessageSegment.image(f'file:///{os.path.abspath(self.path)}')
        else:
            try:
                return MessageSegment.image(util.pic2b64(self.open()))
            except Exception as e:
                salmon.logger.exception(e)
                return MessageSegment.text('[图片出错]')

    def open(self) -> Image:
        try:
            return Image.open(self.path)
        except FileNotFoundError:
            salmon.logger.error(f'缺少图片资源：{self.path}')
            raise


def get(path, *paths):
    return ResObj(os.path.join(path, *paths))

def img(path, *paths):
    return ResImg(os.path.join('img', path, *paths))

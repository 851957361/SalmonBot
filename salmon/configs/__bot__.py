"""请根据注释编辑图片和功能配置，
然后将文件夹config_example重命名为config

※bot监听的端口与ip等请将根目录下的.env.dev.example重命名为.env.dev并编辑配置
"""

DEBUG = False           # log日志调试模式

SUPERUSERS = [1351495774]    # 填写超级用户的QQ号，可填多个用半角逗号","隔开

# 发送图片的协议
# 可选 http, file, base64
# 当cqhttp与bot端不在同一台计算机时，可用http协议
RES_PROTOCOL = 'file'
# 资源库文件夹，需可读可写，windows下注意反斜杠转义
RES_DIR = r'C:/bot/res/'
# 使用http协议时需填写，原则上该url应指向RES_DIR目录
RES_URL = 'http://127.0.0.1:5000/static/'

# 启用的模块
# 初次尝试部署时请先保持默认
# 如欲启用新模块，请认真阅读部署说明，逐个启用逐个配置
# 切忌一次性开启多个
MODULES_ON = {
    'botmanage',
    'priconne',
    'dice',
    'groupmaster',
    # 'setu',
    # 'translate',
    # 'twitter',
}
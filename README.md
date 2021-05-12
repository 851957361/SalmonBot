# SalmonBot

A QQbot for Princess Connect Re:Dive (and other usage :) based on nonebot2.


## 简介

**SalmonBot:**  [Hoshinobot](https://github.com/Ice-Cirno/HoshinoBot) 基于 [nonebot2](https://v2.nonebot.dev/next/) 框架的项目。感谢 [Ice-Cirno](https://github.com/Ice-Cirno) 等开发者的帮助!


## 特点

- **简单详细的部署说明，任何人都能独立自主快速部署本开源项目。**
- **与[Hoshinobot](https://github.com/Ice-Cirno/HoshinoBot)几近一致的结构，便于插件功能的移植。**
- **拥有来自[pcrbot 社区](https://github.com/pcrbot)的丰富功能。**


## 功能介绍

**[公主连结☆Re:Dive](http://priconne-redive.jp)公会战规则已变化**

除未实现会战功能外，SalmonBot 的功能与[Hoshinobot](https://github.com/Ice-Cirno/HoshinoBot)大体一致，主要功能有：

- **转蛋模拟**：单抽、十连、抽一井
- **竞技场解法查询**：支持按服务器过滤
- **竞技场结算提醒**
- **Rank推荐表搬运**
- **官方推特转发**
- **官方四格推送**
- **角色别称查询**
- **切噜语编解码**：切噜～♪
- **竞技场余矿查询**
- **[蜜柑计划](http://mikanani.me)番剧更新订阅**
- **入群欢迎**&**退群提醒**
- **复读**
- **掷骰子**
- **精致睡眠套餐**
- **机器翻译**
- **反馈发送**：反馈内容将由bot私聊发送给维护组

> 由于bot的功能会快速迭代开发，使用方式这里不进行具体的说明，请向bot发送"help"查看详细。


-------------

### 功能模块控制

SalmonBot 的功能各群可根据自己的需要进行开关控制，群管理发送 `lssv` 即可查看功能模块的启用状态，使用以下命令进行控制：

```
启用 service-name
禁用 service-name
```


## 部署指南

初次部署可以先在本地尝试，部署成功后再尝试服务器搭建

<details>
  <summary>点击查看 Linux 部署指南</summary>

### Linux 部署

1. 安装 python3.9 并设置 pip :

    #### 安装第三方库

    ```bash
    # CentOS 用户请执行
    yum -y update
    yum -y groupinstall "Development tools"
    yum -y install wget zlib-devel bzip2-devel openssl-devel ncurses-devel sqlite-devel readline-devel tk-devel gcc* libffi-devel make git vim screen

    # Debian 、Ubuntu 用户请执行
    apt -y update
    apt -y install build-essential
    apt -y install -y make libssl-dev zlib1g-dev libbz2-dev libpcre3 libpcre3-dev libreadline-dev libsqlite3-dev wget curl llvm libncurses5-dev libperl-dev libncursesw5-dev xz-utils tk-dev zlib1g libffi-dev liblzma-dev screen git vim openssl gcc
    ```

    #### 安装python3.9

    ```bash
    #  建立新目录
    sudo mkdir /usr/local/python3.9

    # 下载 Python3.9
    wget --no-check-certificate https://www.python.org/ftp/python/3.9.4/Python-3.9.4.tgz

    #  解压安装包
    tar xzvf Python-3.9.4.tgz

    #  进入目录
    cd Python-3.9.4

    #  编译并配置 python3.9.4 的安装目录
    sudo ./configure --prefix=/usr/local/python3.9

    #  编译安装
    sudo make && make install
    ```

    > 关于`--prefix=/`：
    > 作用是指定安装路径。
    > 不指定prefix，则可执行文件默认放在`/usr/local/bin`，库文件默认放在`/usr/local/lib`，配置文件默认放在`/usr/local/etc`，其它的资源文件放在`/usr/local/share`
    > 若卸载这个程序，需要在原来的make目录下用一次`make uninstall`(前提是make文件指定过uninstall)，或者去上述目录里面把相关的文件一个个删掉。 指定prefix，直接删掉一个文件夹即可。
    > 
    > 如果命令`./configure --prefix=/usr/local/python3.9`报以下错误：`-bash: ./configure: No such file or directory`
    > 使用命令`find -name configure`来查找目录。
    > 若目录下有makefile文件，直接使用`make`编译，`make install`安装；若有setup、install等sh文件或其它可执行文件，则改为直接执行该文件。

    #### 创建软链接

    ```bash
    sudo ln -s /usr/local/python3.9/bin/python3 /usr/bin/python3.9
    ```

    #### 验证安装

    ```bash
    python3.9 -V
    ```

    #### 安装pip并验证安装

    ```bash
    python3.9 -m pip install --user --upgrade pip
    # 或者
    python3.9 get-pip.py

    # 创建软链接
    sudo ln -s /usr/local/python3.9/bin/pip3 /usr/bin/pip3.9

    # 验证安装
    pip3.9 -V
    ```

2. 部署 CQHTTP Mirai 或 go-cqhttp (以go-cqhttp为例):

    #### 下载go-cqhttp

    ```bash
    # 进入到用户文件夹
    cd

    # 创建 go-cqhttp 文件夹并将工作路径切换到这个文件夹
    mkdir go-cqhttp&&cd go-cqhttp

    # 下载稳定版本，若需要使用最新版本请访问 https://github.com/Mrs4s/go-cqhttp/releases
    wget https://github.com/Mrs4s/go-cqhttp/releases/download/v0.9.39/go-cqhttp-v0.9.39-linux-amd64.tar.gz

    # 解压包
    tar xzvf go-cqhttp-v0.9.34-linux-amd64.tar.gz

    # 添加 go-cqhttp 执行权限
    chmod +x go-cqhttp

    # 初次运行 go-cqhttp 时会在当前目录下生成配置文件 config.hjson
    ./go-cqhttp
    ```

    > 使用命令行参数`update`即可更新 go-cqhttp 至最新版：`./go-cqhttp update`
    > 使用命令行参数`faststart`即可跳过 go-cqhttp 启动的延时：`./go-cqhttp faststart`

    #### 配置go-cqhttp

    编辑配置文件 config.hjson

    ```bash
    nano config.hjson
    ```

    > 除 nano 命令外，您也可使用 vim 命令编辑文件。若您从未使用过，推荐使用 nano 
    >
    > 此外也可以使用 ftp 相关工具连接 Linux 服务器后用本地编辑器编辑服务器文件，编辑器的下载安装请参考 Windows 部署

    Salmonbot 使用反向 websocket 与 go-cqhttp 通信, 所以对配置文件中的反向 websocket 部分进行配置，下面的配置可供参考。

    其他配置可参考 go-cqhttp 的[配置文档](https://docs.go-cqhttp.org/guide/config.html#%E9%85%8D%E7%BD%AE)

    ```hjson
    {
        heartbeat_interval: 3
        force_fragmented: true
        ws_reverse_servers: [
            {
                enabled: true
                reverse_url: ws://127.0.0.1:8080/cqhttp/ws
                reverse_reconnect_interval: 3000
            }
        ]
    }
    ```

    > 如果您不清楚某项设置的作用，请保持默认。

3. 输入以下命令克隆本仓库并安装依赖:

    ```bash
    # 进入到用户文件夹
    cd

    # clone 本仓库
    git clone https://github.com/Watanabe-Asa/SalmonBot.git

    # 进入目标文件夹
    cd Salmonbot

    # 安装项目依赖
    python3.9 -m pip install -r requirements.txt
    ```

    >若此处有报错信息，请务必解决，将错误信息复制到搜索引擎搜索一般即可找到解决办法。  
    >
    >若安装 python 依赖库时下载速度缓慢，可以尝试使用命令`python3.9 -m pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt`

4. 编辑 Salmonbot 相关配置：

    ```bash
    # 复制并编辑基础配置，ip与端口与 go-cqhttp 配置保持一致
    cp -r .env.dev.example .env.dev
    nano .env.dev

    # 复制并按照注释编辑模块配置
    cp -r salmon/configs_example salmon/configs
    nano salmon/configs/__bot__.py
    ```

    > 如果您不清楚某项设置的作用，请保持默认。
    >
    > 图片资源请于本项目[releases](https://github.com/Watanabe-Asa/SalmonBot/releases)下载压缩包后解压至任意文件夹，并在`salmon/configs/__bot__.py`中编辑配置该路径。

5. 使用 screen (仅供参考，您也可以使用其他窗口工具)运行 Salmonbot 和 go-cqhttp ：

    <details>
      <summary>点击查看 screen 常用命令</summary>

    ```bash
    screen -S yourname      # 新建一个名为yourname的screen作业
    screen -ls              # 列出当前所有的screen作业
    screen -r yourname      # 回到yourname这个screen作业
    screen -d yourname      # 将yourname这个screen作业离线
    screen -d -r yourname   # 结束当前作业并回到yourname的作业
    screen -wipe            # 检查目前所有的screen作业，并删除已经无法使用的screen作业
    ```

    > 在每个screen作业下，所有命令都以`ctrl+a(C-a)`开始，输入`C-a ?`可以显示所有键绑定信息

    </details>

    #### 安装 screen :

    ```bash
    # CentOS 用户使用此命令安装 screen
    yum install screen
    # Debian 、Ubuntu 用户此命令安装 screen
    apt-get install screen
    ```

    #### 启动 go-cqhttp :

    ```bash
    # 创建一个新的作业用于运行 go-cqhttp 
    screen -S go-cqhttp

    # 进入 go-cqhttp 目录
    cd ~/go-cqhttp

    # 运行 go-cqhttp
    ./go-cqhttp

    # 使用组合键 Ctrl + a , d 挂起这个作业
    ```

    #### 启动 Salmonbot :

    ```bash
    # 创建一个新的作业用于运行 Salmonbot
    screen -S salmon

    # 进入 Salmonbot 目录
    cd ~/Salmonbot

    # 运行 Salmonbot
    python3.9 run.py

    # 使用组合键 Ctrl + a , d 挂起这个作业
    ```

    私聊机器人发送`在？`，若机器人有回复，恭喜您！您已经成功搭建起SalmonBot了。之后您可以尝试发送help查看一般功能的相关说明。

</details>

<details>
  <summary>点击查看 Windows 部署指南</summary>

### Windows 部署

1. 安装下面的软件/工具：

    - Python 3.9：https://www.python.org/downloads/windows/
    - Git：https://git-scm.com/download/win

    > 注意安装 python 时勾选添加到环境变量(Add Python3.9 To System Path)

    编辑器可以选择以下其一安装使用：

    - Visual Studio Code：https://code.visualstudio.com/
    - Notepad++：https://notepad-plus-plus.org/downloads/

2. 下载 CQHTTP Mirai 或 go-cqhttp (以 go-cqhttp 为例):

    - CQHTTP Mirai：https://github.com/yyuueexxiinngg/onebot-kotlin
    - go-cqhttp：https://github.com/Mrs4s/go-cqhttp/

3. 部署 CQHTTP Mirai 或 go-cqhttp (以 go-cqhttp 为例)：

    运行 go-cqhttp.exe ，(右键通过编辑器打开)编辑在当前目录下生成的配置文件 config.hjson 或 config.yml 。
    
    Salmonbot 使用反向 websocket 与 go-cqhttp 通信, 所以对配置文件中的反向 websocket 部分进行配置，下面的配置可供参考。

    ```hjson
    {
        heartbeat_interval: 3
        force_fragmented: true
        ws_reverse_servers: [
            {
                enabled: true
                reverse_url: ws://127.0.0.1:8080/cqhttp/ws
                reverse_reconnect_interval: 3000
            }
        ]
    }
    ```

    > 如果您不清楚某项设置的作用，请保持默认。

4. 打开一个合适的文件夹，点击资源管理器左上角的 `文件 -> 打开Windows Powershell`

5. 依次输入以下命令克隆本仓库并安装依赖：

    ```powershell
    git clone https://github.com/Watanabe-Asa/SalmonBot.git
    cd SalmonBot
    py -3.9 -m pip install -r requirements.txt
    ```

    >若此处有报错信息，请务必解决，将错误信息复制到搜索引擎搜索一般即可找到解决办法。  
    >
    >若安装 python 依赖库时下载速度缓慢，可以尝试使用命令`py -3.9 -m pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt`

6. 回到资源管理器，将`.env.dev.example`文件夹重命名为`.env.dev`，然后右键使用编辑器打开进行编辑。注意ip与端口应与 go-cqhttp 配置保持一致。

7. 进入`salmon`文件夹，将`configs_example`文件夹重命名为`configs`，然后右键使用编辑器打开其中的`__bot__.py`，按照其中的注释说明进行编辑。

    > 如果您不清楚某项设置的作用，请保持默认。
    >
    > 图片资源请于本项目[releases](https://github.com/Watanabe-Asa/SalmonBot/releases)下载压缩包后解压至任意文件夹，并在`__bot__.py`中编辑配置该路径。

8. 回到powershell，启动 Salmonbot :

    ```powershell
    py -3.9 run.py
    ```

9. 重新运行 go-cqhttp.exe。若提示异地登陆验证，按照提示完成扫码或滑块验证。

    私聊机器人发送`在？`，若机器人有回复，恭喜您！您已经成功搭建起SalmonBot了。之后您可以尝试发送help查看一般功能的相关说明。

</details>



### 更进一步

现在，机器人已经可以使用`模拟抽卡`等基本功能了。但还无法使用`竞技场查询`、`番剧订阅`、`推特转发`等功能。这是因为，这些功能需要相应的api key。相应api key获取有难有易，您可以根据自己的需要去获取。

下面将会分别介绍功能的配置与api key的获取方法：



#### pcrdfans授权key

竞技场查询功能的数据来自 [公主连结Re: Dive Fan Club - 硬核的竞技场数据分析站](https://pcrdfans.com/)，使用 pcrdfans 提供的查询功能需要 pcrdfans 的授权key。

您可以在[这里](https://pcrdfans.com/bot)申请授权key。现在申请渠道**已关闭**。

如果您已经有了授权key , 在文件`salmon/configs/priconne.py`中填写您的key：

    ```python
    class arena:
        AUTH_KEY = "your_key"
    ```



#### 蜜柑番剧 RSS Token

> 请先在`salmon/configs/__bot__.py`的`MODULES_ON`中取消`mikan`的注释  
> 本功能默认关闭，在群内发送 "启用 bangumi" 即可开启

番剧订阅数据来自 [蜜柑计划 - Mikan Project](https://mikanani.me/)，您可以注册一个账号，添加订阅的番剧，之后点击 Mikan 首页的 RSS订阅 ，复制类似于下面的url地址：

    ```
    https://mikanani.me/RSS/MyBangumi?token=abcdfegABCFEFG%2b123%3d%3d
    ```

保留其中的`token`参数，在文件`salmon/configs/mikan.py`中填写您的token：

    ```python
    MIKAN_TOKEN = "abcdfegABCFEFG+123=="
    ```

> 注意：您需要将 token 部分的`%2b`替换为`+`，将`%2f`替换为`/`，将`%3d`替换为`=`。



#### 推特转发

推特转发功能需要推特开发者账号，具体申请方法请自行[Google](http://google.com)。注：现在推特官方大概率拒绝来自中国大陆的新申请，自备海外手机号及大学邮箱可能会帮到您。

若您已有推特开发者账号，在文件`salmon/configs/twitter.py`中填写您的key：

    ```python
    consumer_key = "your_consumer_key",
    consumer_secret = "your_consumer_secret",
    access_token_key = "your_access_token_key",
    access_token_secret = "your_access_token_secret"
    ```



#### 设置入群欢迎

您可以在文件`salmon/configs/groupmaster.py`中设置群聊的入群欢迎：

    ```python
    increase_welcome = {
        "default": "欢迎入群！你已经是群大佬了, 快来跟群萌新打个招呼吧~",
        114514191: "欢迎来到 下北泽群 !",
        145141919: "欢迎来到 红茶交流群 !",
        141919810: "欢迎来到 下北泽红茶群 !",
    }
    ```




## 关于开源

本项目以 GPL-3.0 协议开源。

如果您在部署过程中遇到任何问题，欢迎加入QQ交流群1128254624讨论。



## 致谢

感谢以下开发者及其项目对本项目的帮助：

**Ice-Cirno**: https://github.com/Ice-Cirno/HoshinoBot

**AkiraXie**: https://github.com/AkiraXie/hoshino.nb2

**Lancercmd**: https://github.com/Lancercmd/nonebot_plugin_translator

**Chendihe4975**: https://github.com/Chendihe4975/Yuudi




## 友情链接

**Hoshinobot**: https://github.com/Ice-Cirno/HoshinoBot

**干炸里脊资源站**: https://redive.estertion.win/

**公主连结Re: Dive Fan Club - 硬核的竞技场数据分析站**: https://pcrdfans.com/

**yobot**: https://yobot.win/
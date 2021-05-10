# Arknights-gacha-simulator
明日方舟抽卡模拟机器人
使用方法:
  1.安装mirai和http插件
  2.安装此项目python运行库
  3.将app = GraiaMiraiApplication(
        broadcast=bcc,
        connect_info=Session(
            host="http://localhost:8080", # 填入 httpapi 服务运行的地址
            authKey="***********", # 填入 authKey
            account=5555555555, # 你的机器人的 qq 号
            websocket=False # Graia 已经可以根据所配置的消息接收的方式来保证消息接收部分的正常运作.
        )
    )
    改为你自己的参数
 4.运行mirai, python main.py运行此项目

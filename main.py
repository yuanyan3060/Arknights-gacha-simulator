from graia.broadcast import Broadcast
from graia.application import GraiaMiraiApplication, Session
from graia.application.message.chain import MessageChain
import asyncio
import aiofiles
from graia.application.message.elements.internal import Xml
from graia.application.message.elements.internal import At
from graia.application.message.elements.internal import Image 
from graia.application.message.elements.internal import Plain
from graia.application.message.elements.internal import Voice_LocalFile
from graia.application.friend import Friend
from graia.application.group import Group, Member


from graia.scheduler import GraiaScheduler
from graia.scheduler import timers
import graia.scheduler as scheduler

import os
import random
import cv2
import numpy as np
import json
import requests
import time
#from graiax import silkcoder
class user_data:
    path = "./user_data.json"
    data = {}
    def __init__(self):
        asyncio.run(self.read())

    async def read(self):
        async with aiofiles.open(self.path, "r", encoding="utf-8") as fp:
            self.data = json.loads(await fp.read())

    async def save(self):
        async with aiofiles.open(self.path, "w", encoding="utf-8") as fp:
            await fp.write(json.dumps(self.data, ensure_ascii=False))

    async def change(self, id, name, rarity, char):
        id = str(id)
        rarity = str(rarity)
        char = char[:-4]
        if id not in self.data:
            self.data[id]={
                "name":name,
                "1":{},
                "2":{},
                "3":{},
                "4":{},
                "5":{},
                "6":{},
                "times":0,
                "fulltimes":0
            } 
        if char not in self.data[id][rarity]:
            self.data[id][rarity][char]=1
        else:
            self.data[id][rarity][char]=self.data[id][rarity][char]+1
        
        if rarity=="6":
            self.data[id]["times"]=0
        else:
            self.data[id]["times"]=self.data[id]["times"]+1

        if "fulltimes" in self.data[id]:
            self.data[id]["fulltimes"]= self.data[id]["fulltimes"]+1
        else:
            self.data[id]["fulltimes"]=1
        await self.save()
    
    def delete(self, id):
        id = str(id)
        if id in self.data:
            del self.data[id]
        
    
    def get_times(self, id):
        id = str(id)
        if id in self.data:
            return self.data[id]["times"]
        else:
            return 0

    def query(self, id, name):
        id = str(id)
        if id in self.data:
            times = self.data[id]["times"]
            fulltimes = self.data[id].get("fulltimes", "未能获取")
            result = "号码: {}\n".format(id)
            #result = "号码: {}\n".format("**********")
            result = result+"昵称: {}\n".format(name)
            result = result+"已有六星: {}\n\n".format(", ".join(self.data[id]["6"]))
            result = result+"已有五星: {}\n\n".format(", ".join(self.data[id]["5"]))
            result = result+"已有四星: {}\n\n".format(", ".join(self.data[id]["4"]))
            result = result+"已有三星: {}\n\n".format(", ".join(self.data[id]["3"]))
            result = result+"总抽卡次数: {}\n".format(fulltimes)
            result = result+"距离上次抽出六星次数: {}\n".format(times)
            result = result+"抽出六星概率: {}%".format(2*(times-19) if times>20 else 2)
        else:
            result = "号码: {}\n".format(id)
            result = result+"昵称: {}\n".format(name)
            result = result+"未查询到相关信息"
        return result
    
async def async_imread(path):
    async with aiofiles.open(path, "rb") as fp:
        img_data = await fp.read()
    return cv2.imdecode(np.frombuffer(img_data, dtype='uint8'), cv2.IMREAD_UNCHANGED)

async def ten_img_make(rarity_list, char_list):
    tmp_dict = {
        1:["一星"],
        2:["二星"],
        3:["三星"],
        4:["四星"],
        5:["五星"],
        6:["六星"]
    }
    for i in range(10):
        tmp_dict[rarity_list[i]].append(char_list[i][:-4])
        base[0:580,28+i*122:150+i*122]= await async_imread("chars_r2/{}/{}".format(rarity_list[i], char_list[i]))
        base[580:,28+i*122:150+i*122]=rarity_img[rarity_list[i]-1][580:,28+i*122:150+i*122]
    img_encode = cv2.imencode('.jpg', base)[1]
    data_encode = np.array(img_encode)  
    str_encode = data_encode.tobytes() 
    result_str = ""
    cnt = 0
    for i in range(6, 0, -1):
        if len(tmp_dict[i])>1:
            cnt = cnt + len(tmp_dict[i])-1
            result_str = result_str + tmp_dict[i][0] + ": " + ", ".join(tmp_dict[i][1:])
            if cnt < 10:
                result_str = result_str + "\n"
    return str_encode, result_str


async def gacha(up=None, times=0):
    rarity = None
    text = None
    six_probability =0.02
    if times>20:
        six_probability = 0.02*(times-19)
    if random.random()<=six_probability:
        rarity = 6
    elif random.random()<=six_probability+(1-six_probability)*(8/98):
        rarity = 5
    elif random.random()<=six_probability+(1-six_probability)*(56/98):
        rarity = 4
    else:
        rarity = 3
    chars = os.listdir("chars/{}".format(rarity))
    char = random.choice(chars)
    if rarity ==6:
        tmp = random.random()
        if tmp<0.4:
            char="凯尔希.png"
        elif tmp<0.8:
            char="浊心斯卡蒂.png"
    if up:
        if random.random()<=0.5 and up+".png" in chars:
            char = up+".png"
    return rarity, char

loop = asyncio.get_event_loop()
bcc = Broadcast(loop=loop)
app = GraiaMiraiApplication(
    broadcast=bcc,
    connect_info=Session(
        host="http://localhost:8080", # 填入 httpapi 服务运行的地址
        authKey="***********", # 填入 authKey
        account=5555555555, # 你的机器人的 qq 号
        websocket=False # Graia 已经可以根据所配置的消息接收的方式来保证消息接收部分的正常运作.
    )
)

@bcc.receiver("GroupMessage")
async def group_message_listener(app: GraiaMiraiApplication, group: Group, message: MessageChain, member:Member):
    if message.asDisplay()=="单抽":
        times = user.get_times(member.id)
        rarity, char = await gacha(times=times)
        await user.change(member.id, member.name, rarity, char)
        await app.sendGroupMessage(group, MessageChain.create([
            Image.fromLocalFile("chars/{}/{}".format(rarity, char)),
            Plain(text="{}: {}".format(rarity_text_dict[rarity], char[:-4]))
            ]))
    elif message.asDisplay()=="十连":
        rarity_list, char_list= [], []
        for i in range(10):
            times = user.get_times(member.id)
            rarity, char = await gacha(times=times)
            await user.change(member.id, member.name, rarity, char)
            rarity_list.append(rarity)
            char_list.append(char)
        result_file, result_str = await ten_img_make(rarity_list, char_list)
        await app.sendGroupMessage(group, MessageChain.create([
            Image.fromUnsafeBytes(result_file),
            Plain(text=result_str)
            ]))
        if "浊心斯卡蒂.png" in char_list:
            await app.sendGroupMessage(group, MessageChain.create([
                Voice_LocalFile(filepath= "浊心斯卡蒂_干员报到.amr")
                ]))
            await app.sendGroupMessage(group, MessageChain.create([
                Plain(text="我在等你，博士。我等你太久，太久了，我甚至已经忘了为什么要在这里等你......不过这些都不重要了。不再那么重要了。")
                ]))
    elif message.asDisplay().startswith("查询"):
        await app.sendGroupMessage(group, MessageChain.create([
            Plain(text=user.query(member.id, member.name))
            ]))

    elif message.asDisplay()=="清除":
        user.delete(member.id)
        await app.sendGroupMessage(group, MessageChain.create([
            Plain(text="号码: {}\n昵称: {}\n清除完成".format(member.id, member.name))
            ]))

            

@bcc.receiver("FriendMessage")
async def friend_message_listener(app: GraiaMiraiApplication, friend: Friend, message: MessageChain):
    if message.asDisplay()=="单抽":
        times = user.get_times(friend.id)
        rarity, char = await gacha(times=times)
        await user.change(friend.id, friend.nickname, rarity, char)
        await app.sendFriendMessage(friend, MessageChain.create([
            Image.fromLocalFile("chars/{}/{}".format(rarity, char)),
            Plain(text="{}: {}".format(rarity_text_dict[rarity], char[:-4]))
            ]))
    elif message.asDisplay()=="十连":
        rarity_list, char_list= [], []
        for i in range(10):
            times = user.get_times(friend.id)
            rarity, char = await gacha(times=times)
            await user.change(friend.id, friend.nickname, rarity, char)
            rarity_list.append(rarity)
            char_list.append(char)
        result_file, result_str = await ten_img_make(rarity_list, char_list)
        await app.sendFriendMessage(friend, MessageChain.create([
            Image.fromUnsafeBytes(result_file),
            Plain(text=result_str)
            ]))
    elif message.asDisplay().startswith("查询"):
        await app.sendFriendMessage(friend, MessageChain.create([
            Plain(text=user.query(friend.id, friend.nickname))
            ]))

    elif message.asDisplay()=="清除":
        user.delete(friend.id)
        await app.sendFriendMessage(friend, MessageChain.create([
            Plain(text="号码: {}\n昵称: {}\n清除完成".format(friend.id, friend.nickname))
            ]))



base = asyncio.run(async_imread("rarity/1.png"))
rarity_img = []
user = user_data()
rarity_text_dict = {
            6:"六星",
            5:"五星",
            4:"四星",
            3:"三星",
        } 

for i in range(1, 7):
    rarity_img.append(asyncio.run(async_imread("rarity/{}.png".format(i))))

app.launch_blocking()

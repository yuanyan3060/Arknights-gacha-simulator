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
            fulltimes = self.data[id].get("fulltimes", "????????????")
            result = "??????: {}\n".format(id)
            #result = "??????: {}\n".format("**********")
            result = result+"??????: {}\n".format(name)
            result = result+"????????????: {}\n\n".format(", ".join(self.data[id]["6"]))
            result = result+"????????????: {}\n\n".format(", ".join(self.data[id]["5"]))
            result = result+"????????????: {}\n\n".format(", ".join(self.data[id]["4"]))
            result = result+"????????????: {}\n\n".format(", ".join(self.data[id]["3"]))
            result = result+"???????????????: {}\n".format(fulltimes)
            result = result+"??????????????????????????????: {}\n".format(times)
            result = result+"??????????????????: {}%".format(2*(times-19) if times>20 else 2)
        else:
            result = "??????: {}\n".format(id)
            result = result+"??????: {}\n".format(name)
            result = result+"????????????????????????"
        return result
    
async def async_imread(path):
    async with aiofiles.open(path, "rb") as fp:
        img_data = await fp.read()
    return cv2.imdecode(np.frombuffer(img_data, dtype='uint8'), cv2.IMREAD_UNCHANGED)

async def ten_img_make(rarity_list, char_list):
    tmp_dict = {
        1:["??????"],
        2:["??????"],
        3:["??????"],
        4:["??????"],
        5:["??????"],
        6:["??????"]
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
            char="?????????.png"
        elif tmp<0.8:
            char="???????????????.png"
    if up:
        if random.random()<=0.5 and up+".png" in chars:
            char = up+".png"
    return rarity, char

loop = asyncio.get_event_loop()
bcc = Broadcast(loop=loop)
app = GraiaMiraiApplication(
    broadcast=bcc,
    connect_info=Session(
        host="http://localhost:8080", # ?????? httpapi ?????????????????????
        authKey="***********", # ?????? authKey
        account=5555555555, # ?????????????????? qq ???
        websocket=False # Graia ?????????????????????????????????????????????????????????????????????????????????????????????.
    )
)

@bcc.receiver("GroupMessage")
async def group_message_listener(app: GraiaMiraiApplication, group: Group, message: MessageChain, member:Member):
    if message.asDisplay()=="??????":
        times = user.get_times(member.id)
        rarity, char = await gacha(times=times)
        await user.change(member.id, member.name, rarity, char)
        await app.sendGroupMessage(group, MessageChain.create([
            Image.fromLocalFile("chars/{}/{}".format(rarity, char)),
            Plain(text="{}: {}".format(rarity_text_dict[rarity], char[:-4]))
            ]))
    elif message.asDisplay()=="??????":
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
        if "???????????????.png" in char_list:
            await app.sendGroupMessage(group, MessageChain.create([
                Voice_LocalFile(filepath= "???????????????_????????????.amr")
                ]))
            await app.sendGroupMessage(group, MessageChain.create([
                Plain(text="??????????????????????????????????????????????????????????????????????????????????????????????????????......??????????????????????????????????????????????????????")
                ]))
    elif message.asDisplay().startswith("??????"):
        await app.sendGroupMessage(group, MessageChain.create([
            Plain(text=user.query(member.id, member.name))
            ]))

    elif message.asDisplay()=="??????":
        user.delete(member.id)
        await app.sendGroupMessage(group, MessageChain.create([
            Plain(text="??????: {}\n??????: {}\n????????????".format(member.id, member.name))
            ]))

            

@bcc.receiver("FriendMessage")
async def friend_message_listener(app: GraiaMiraiApplication, friend: Friend, message: MessageChain):
    if message.asDisplay()=="??????":
        times = user.get_times(friend.id)
        rarity, char = await gacha(times=times)
        await user.change(friend.id, friend.nickname, rarity, char)
        await app.sendFriendMessage(friend, MessageChain.create([
            Image.fromLocalFile("chars/{}/{}".format(rarity, char)),
            Plain(text="{}: {}".format(rarity_text_dict[rarity], char[:-4]))
            ]))
    elif message.asDisplay()=="??????":
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
    elif message.asDisplay().startswith("??????"):
        await app.sendFriendMessage(friend, MessageChain.create([
            Plain(text=user.query(friend.id, friend.nickname))
            ]))

    elif message.asDisplay()=="??????":
        user.delete(friend.id)
        await app.sendFriendMessage(friend, MessageChain.create([
            Plain(text="??????: {}\n??????: {}\n????????????".format(friend.id, friend.nickname))
            ]))



base = asyncio.run(async_imread("rarity/1.png"))
rarity_img = []
user = user_data()
rarity_text_dict = {
            6:"??????",
            5:"??????",
            4:"??????",
            3:"??????",
        } 

for i in range(1, 7):
    rarity_img.append(asyncio.run(async_imread("rarity/{}.png".format(i))))

app.launch_blocking()

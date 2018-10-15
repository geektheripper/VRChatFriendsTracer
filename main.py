#coding=utf-8
import os
from concurrent import futures
from api.vrchat import VRChatAPI
from  threading import Thread
from utils.utils import logging
from settings import *
from models.redis_model import UserModel
from models.mysql_model import Log
from models import rserver
import pickle
import time

class VRchat:
    def __init__(self):
        self.api=VRChatAPI.init()
        self.rserver=rserver
    def log(self,User,text,target):
        logging.info(MSG_TEXT_FORMAT%(User.displayName,text,target))
        l=Log(User.id,User.displayName,text,target)
        t=Thread(target=l.save)
        t.start()

    def check_status(self):
        data=self.api.get_online_friends()
        for user in data:
            User=UserModel(user)
            keyname=REDIS_KEY_UID%User.id
            if not self.rserver.exists(keyname):
                self.rserver.set(keyname, pickle.dumps(User), ex=REDIS_KEY_EXP)
                self.log(User,"上线了", self.get_world_name(User.location))
            else:
                oldUser=pickle.loads(self.rserver.get(keyname))
                if oldUser.location!=User.location:
                    self.log(User,"进入了世界", self.get_world_name(User.location))
                if oldUser.currentAvatarImageUrl!=User.currentAvatarImageUrl:
                    self.log(User,"更换了角色", User.currentAvatarImageUrl)
                if oldUser.status!=User.status:
                    self.log(User,"更改了个人状态", User.status)
                if  oldUser.statusDescription!=User.statusDescription:
                    self.log(User,"更改了个人描述", User.statusDescription)

                self.rserver.set(keyname, pickle.dumps(User), ex=REDIS_KEY_EXP)
    def get_world_name(self,location):
        if ":" in location:
            wid,id=location.split(":")
            if "~" in id:
                id,*args=id.split("~")
            name=self.rserver.hget(REDIS_KEY_WORLD,wid)
            if name is None:
                name=self.api.get_world_name(wid)
                if name:
                    self.rserver.hset(REDIS_KEY_WORLD,key=wid,value=name.encode("utf8"))
            else:name=name.decode("utf8")
            return "%s:%s"%(name,id)
        else:
            return location
    def rcv_redis_message(self):
        pubsub = self.rserver.pubsub()
        pubsub.psubscribe('*')
        logging.info('Starting message loop')
        while True:
            message = pubsub.get_message()
            if message:
                try:
                    data=message['data'].decode("utf8")
                except:pass
                else:
                    if "Online" in data:
                        usr_id=data.split("Online:")[-1]
                        usr_name=self.api.get_user_name(usr_id)
                        logging.info(MSG_TEXT_FORMAT% (usr_name, "下线了",'offline'))
                        l = Log(usr_id,usr_name,"下线了","offline")
                        t = Thread(target=l.save)
                        t.start()
            else:
                time.sleep(0.1)

    def loop(self):
        msg = Thread(target=self.rcv_redis_message)
        msg.start()
        while True:

           with futures.ThreadPoolExecutor(max_workers=1) as executor:
               f=executor.submit(self.check_status)

           time.sleep(LOOP_DELAY)

           try:
                r=f.result()
           except Exception as e:
                logging.exception(e)
                logging.info("尝试重新初始化")
                if os.path.exists("session.pkl"):
                    os.remove("session.pkl")
                self.__init__()

if __name__ == '__main__':
    vrc=VRchat()
    vrc.loop()

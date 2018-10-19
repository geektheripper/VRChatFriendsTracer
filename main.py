#coding=utf-8
import os
from multiprocessing import Process
from concurrent import futures
from api.vrchat import VRChatAPI
from  threading import Thread
from utils.utils import logging
from settings import *
from secure import DISCORD_TOKEN
from models.redis_model import UserModel
from models.mysql_model import Log,StatusText
from models import rserver
import pickle
import time
class VRchat:
    def __init__(self):
        self.api=VRChatAPI.init()
        self.rserver=rserver
    def logger(self,User,text,target):
        msg=MSG_TEXT_FORMAT%(User.displayName,text,target)
        logging.info(msg)
        log=Log(User.id,User.displayName,text,target)
        self.rserver.rpush(REDIS_NOTIFICATION_QUEUE,pickle.dumps(log))
        t=Thread(target=log.save)
        t.start()


    def check_status(self):
        data=self.api.get_online_friends()
        for user in data:
            User=UserModel(user)
            keyname=REDIS_KEY_UID%User.id
            if not self.rserver.exists(keyname):
                self.rserver.set(keyname, pickle.dumps(User), ex=REDIS_KEY_EXP)
                self.logger(User,StatusText.Online.value, self.get_world_name(User.location))
            else:
                oldUser=pickle.loads(self.rserver.get(keyname))
                if oldUser.location!=User.location:
                    self.logger(User,StatusText.ChangeWorld.value, self.get_world_name(User.location))
                if oldUser.currentAvatarImageUrl!=User.currentAvatarImageUrl:
                    self.logger(User,StatusText.ChangeAvatar.value, User.currentAvatarImageUrl)
                if oldUser.status!=User.status:
                    self.logger(User,StatusText.ChangeStatus.value, User.status)
                if  oldUser.statusDescription!=User.statusDescription:
                    self.logger(User,StatusText.ChangeDescription.value, User.statusDescription)

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
                    self.rserver.hset(REDIS_KEY_WORLD,key=wid,value=name)
            else:name=name.decode('utf8')
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
                    if ":" in data:
                        User=UserModel()
                        User.id=data.split(":")[-1]
                        User.displayName=self.api.get_user_name(User.id)
                        self.logger(User,StatusText.Offline.value,StatusText.OfflineText.value)

            else:
                time.sleep(BOT_LOOP_DELAY)

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

def bot():
    from bot.bot import VRCBot
    bot = VRCBot()
    bot.run(DISCORD_TOKEN)
if __name__ == '__main__':
    vrc=VRchat()
    t=Process(target=bot)
    t.start()
    vrc.loop()

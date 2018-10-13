#coding=utf-8
from utils.utils import *
import requests
from base64 import b64encode
from utils.utils import *
from settings import *
class VRChatAPI:

    apiKey = 'JlE5Jldo5Jibnk5O5hTx6XVqsJu4WJ26'

    headers = {
        'accept-encoding': 'gzip, deflate, br',
        'accept-language': 'zh-CN,zh;q=0.9,ja;q=0.8,en;q=0.7,zh-TW;q=0.6',
        'user-agent': 'Mo.zilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.36',
        'accept': 'application/json, text/plain, */*',
        'referer': 'https://www.vrchat.net',
          }
    def __init__(self,session):
        self.s=session
    @staticmethod
    def init():
        session=load_session()
        if session:
            api=VRChatAPI(session)
        else:
            session=VRChatAPI.create_session(VRC_USERNAME,VRC_PASSWORD)
            api=VRChatAPI(session)
        return api
    @staticmethod
    def create_session(uname,pwd):
        session=requests.session()
        resp=VRChatAPI.login(session,uname,pwd)
        dump_session(session)
        return session

    @classmethod
    @resp2json
    def login(cls,session,uname,pwd):
        auth = {'authorization': 'Basic ' + b64encode(":".join([uname, pwd]).encode('utf8')).decode('utf8')}
        params={'apiKey':cls.apiKey}
        session.headers.update(cls.headers)
        resp = session.get('https://www.vrchat.net/api/1/auth/user',params=params,headers=auth)
        return resp

    @resp2json
    def _get_friends(self,offline,n,offset):
        params = {
            'offline':{True:"true",False:"false"}[offline],
            'n': n,
            'offset':offset,
        }
        resp = self.s.get('https://www.vrchat.net/api/1/auth/user/friends' ,params=params)
        return resp

    def _get_all_friends(self,offline):
        offset=0
        n=25
        tdata=[]
        while True:
            data=self._get_friends(offline=offline,n=n,offset=offset)
            tdata.extend([i for i in data])
            if len(data)==n:
               offset+=25
            else:
                break
        return tdata


    def get_online_friends(self):
        return self._get_all_friends(offline=False)
    def get_offline_friends(self):
        return self._get_all_friends(offline=True)

    @resp2json
    def get_user_info(self,user_id):
        resp=self.s.get("https://www.vrchat.net/api/1/users/{}".format(user_id))
        return resp

    @resp2json
    def playemoderations(self,type):
        params={"type":type}
        resp=self.s.get('https://www.vrchat.net/api/1/auth/user/playermoderations',params=params)
        return resp


    @resp2json
    def get_world_info(self,wrld_id):
        resp=self.s.get("https://www.vrchat.net/api/1/worlds/{}".format(wrld_id))
        return resp

    def get_world_name(self,wid):
        data= self.get_world_info(wid)
        return data['name']
    def get_user_name(self,user_id):
        data=self.get_user_info(user_id=user_id)
        return data.get("displayName")


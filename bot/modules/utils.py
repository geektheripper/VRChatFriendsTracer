#coding=utf-8
from models.mysql_model import StatusText
import re
priv={ 0:[],
       1:["StatusText.Online","StatusText.Offline"],
       2:["StatusText.Online","StatusText.Offline","StatusText.ChangeWorld"],
       3:["StatusText.Online","StatusText.Offline","StatusText.ChangeWorld","StatusText.ChangeAvatar"],
       4:["StatusText.Online","StatusText.Offline","StatusText.ChangeWorld","StatusText.ChangeAvatar",'StatusText.ChangeDescription','StatusText.ChangeStatus'],
       }



def nameInMention(name,mentions):
    for key in mentions.keys():
        if key in name.lower():
            return True,key,mentions[key]
    return False,None,None

async def getDisplayName(self,mentions):
    if isinstance(mentions,list):
        displayName=[]
        for mention in mentions:
            mention=mention.replace("!","")
            user=await self.get_user_info(mention[2:-1])
            displayName.append(f'@{user.display_name}')
        return displayName
    elif isinstance(mentions,str):
        mentions = mentions.replace("!", "")
        user = await self.get_user_info(mentions[2:-1])
        return f'@{user.display_name}'
    else:return ""

def Log2Text(Log,channelConfig):
    mentions=channelConfig["mentions"]
    level=channelConfig["level"]
    verbose=channelConfig["verbose"]
    atLevel=channelConfig.get('atlevel',level)
    ret,key,roles=nameInMention(Log.displayName,mentions)
    replyMsg = ""
    if verbose or ret:
        text = str(StatusText(Log.text))
        if text=='StatusText.ChangeAvatar':
            replyMsg= "%(displayName)-15s %(text)-10s \n%(target)s"%Log.__dict__
        elif text=='StatusText.ChangeDescription':
            replyMsg = "%(displayName)-15s %(text)-10s \n%(target)s" % Log.__dict__
        else:
            if len(Log.target)>16:
                Log.target=Log.target[:16]+"…"
                if len(Log.displayName)>14:
                    if re.search("\s[0-9a-f]{4}",Log.displayName[-4:]):
                        Log.displayName=Log.displayName[:-5]
                    if len(Log.displayName)>15:
                        Log.displayName=Log.displayName[:14]+"…"
            replyMsg = "%(displayName)-15s %(text)-10s %(target)s"%Log.__dict__
        if ret:
            replyMsg+="\n"+" ".join(roles)
        if text in priv[level] or (text in priv[atLevel] and ret):
            pass
        else:
                replyMsg=""
    return replyMsg
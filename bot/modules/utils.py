from models.mysql_model import StatusText
import re
priv={1:["StatusText.Online","StatusText.Offline"],
       2:["StatusText.Online","StatusText.Offline","StatusText.ChangeWorld"],
       3:["StatusText.Online","StatusText.Offline","StatusText.ChangeWorld","StatusText.ChangeAvatar"],
       4:["StatusText.Online","StatusText.Offline","StatusText.ChangeWorld","StatusText.ChangeAvatar",'StatusText.ChangeDescription','StatusText.ChangeStatus'],
       }


def get_channel(channels, channel_name):
    for channel in channels:
        if channel.name == channel_name:
            return channel
    return None

def log_to_text(Log,level):
    text = str(StatusText(Log.text))
    if text not in priv[level]:
        return None
    if text=='StatusText.ChangeAvatar':
        return "%(displayName)-15s %(text)-10s \n%(target)s"%Log.__dict__
    elif text=='StatusText.ChangeDescription':
        return "%(displayName)-15s %(text)-10s \n%(target)s" % Log.__dict__
    else:
        if len(Log.target)>16:
            Log.target=Log.target[:16]+"…"
            if len(Log.displayName)>14:
                if re.search("\s[0-9a-f]{4}",Log.displayName[-4:]):
                    Log.displayName=Log.displayName[-5:]
                if len(Log.displayName)>15:
                    Log.displayName=Log.displayName[:14]+"…"
        return "%(displayName)-15s %(text)-10s %(target)s"%Log.__dict__
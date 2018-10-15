import asyncio
from settings import REDIS_NOTIFICATION_QUEUE
from models import rserver
import pickle
from bot.modules.utils import log_to_text
from bot.modules.discordUtils import safeSend

def get_channel(channels, channel_name):
    for channel in channels:
        if channel.name == channel_name:
            return channel
    return None

async def notificationTask(client):
    await client.wait_until_ready()
    print("started")
    while not client.is_closed():
        msg=rserver.rpop(REDIS_NOTIFICATION_QUEUE)

        if msg and client.current_channel is not None:
            try:
                Log=pickle.loads(msg)
            except:pass
            else:
                await safeSend(client.current_channel,text=log_to_text(Log,client.msg_level))
        await asyncio.sleep(0.1)
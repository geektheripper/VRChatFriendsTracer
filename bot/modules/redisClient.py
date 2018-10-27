#coding=utf-8
"""
Async Redis stuff

Redis structure:

Key                       | Value
--------------------------|-----------------------------------------------------
subscribedChannels        | pickled( subscribedChannelList )
launchNotifSent           | True / False as a string
latestLaunchInfoEmbedDict | pickled( launchInfoEmbedDict )
Guild snowflake as a str  | Mentions to ping when a "launching soon" msg is sent
"""

from aredis import StrictRedis
from settings import *
import logging
import pickle


logger = logging.getLogger(__name__)


class redisClient(StrictRedis):
    def __init__(self, host=REDIS_HOST, port=REDIS_PORT, dbNum=0):
        # Uses redis default host, port, and dbnum by default
        super().__init__(host=host, port=port, db=dbNum)
        logger.info(f"Connected to {host}:{port} on db num {dbNum}")

    async def safeGet(self, key, deserialize=False):
        """
        Returns 0 if get(key) fails or a value does not exist for that key
        """
        try:
            value = await self.get(key)
            if not value:
                return 0
            elif deserialize:
                return pickle.loads(value)
            else:
                return value.decode("UTF-8")
        except Exception as e:
            logger.error(f"Failed to safeGet data from Redis: key: {key} error: {type(e).__name__}: {e}")
            return 0


    async def safeSet(self, key, value, serialize=False):
        """
        Returns 0 if set() fails
        """
        try:
            if serialize:
                return await self.set(key, pickle.dumps(value))
            return await self.set(key, value.encode("UTF-8"))
        except Exception as e:
            logger.error(f"Failed to safeSet data in Redis: key: {key} error: {type(e).__name__}: {e}")
            return 0

    async def safeLrange(self, key,start,stop, deserialize=False):
        """
        Returns 0 if get(key) fails or a value does not exist for that key
        """
        try:
            list = await self.lrange(key,start,stop-1)
            if not list:
                return 0
            self.ltrim(key, stop, -1)
            if deserialize:
                return [pickle.loads(i) for i in list]
            else:
                return [i.decode("UTF-8") for i in list]
        except Exception as e:
            logger.error(f"Failed to safeLrange data from Redis: key: {key} error: {type(e).__name__}: {e}")
            return 0

    async def safeLpop(self, key, deserialize=False):
        """
        Returns 0 if LPOP(key) fails or a value does not exist for that key
        """
        try:
            value = await self.lpop(key)
            if not value:
                return 0
            if deserialize:
                return pickle.loads(value)
            else:
                return value.decode("UTF-8")
        except Exception as e:
            logger.error(f"Failed to safeLpop data from Redis: key: {key} error: {type(e).__name__}: {e}")
            return 0

    async def getSubscribedChannelIDs(self):
        """
        Returns a dict: {"list": list, "err": True/False}
        This is so we can return & iterate a list even if there is an error,
        which means in methods where it doesen't matter if there was an error or
        not, we can just ignore it and iterate an empty list instead of having
        to check for an error. e.g. the reaper doesen't care if there was an err
        """
        channels = await self.safeGet("subscribedChannels", deserialize=True)
        if channels or channels == []:
            # An empty list isn't an err
            return {"list": channels, "err": False}
        # Cannot get any subscribed channels so return empty
        return {"list": [], "err": True}

    async def getChannelConfig(self,channelID):
        config=await self.safeGet(REDIS_KEY_DISCORD_CHANNEL_CONFIG%channelID,deserialize=True)
        if config:
            return config
        else:
            await self.setDefaultConfig(channelID)
            await self.getChannelConfig(channelID)

    async  def setDefaultConfig(self,channelID):
        config={'mentions': {}, 'verbose': False, 'level': 1}
        ret=await self.safeSet(REDIS_KEY_DISCORD_CHANNEL_CONFIG%channelID,config,serialize=True)
        if not ret:
            return 0
        return 1
    async def getLog(self):
        Log=await self.safeLpop(REDIS_NOTIFICATION_QUEUE,deserialize=True)
        if Log:
            return Log
        return 0
    async def scanAll(self,match):
        try:
            results = []
            cur, ret = await redisConn.scan(0, match, 1000)
            results += ret
            while cur != 0:
                cur, ret = redisConn.scan(cur, match , 1000)
                results += ret
            if not ret:
                return 0
            return [i.decode('utf8') for i in ret]
        except Exception as e:
            logger.error(f"Failed to scanAll data from Redis: match: {match} error: {type(e).__name__}: {e}")
            return 0



def startRedisConnection():
    # Global so it can be imported after being set to a redisClient instance
    global redisConn
    redisConn = redisClient()
    return redisConn

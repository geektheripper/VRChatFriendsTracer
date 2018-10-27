#coding=utf-8
import asyncio
from settings import BOT_LOOP_DELAY,REAPER_INTERVAL
from bot.modules.utils import Log2Text
from bot.modules.discordUtils import safeSend
from bot.bot import redisConn
import logging
logger = logging.getLogger(__name__)

async def notificationTask(client):
    await client.wait_until_ready()
    logger.info("started")
    while not client.is_closed():
        Log=await redisConn.getLog()
        if Log:
            subbedChannelsDict = await redisConn.getSubscribedChannelIDs()
            if subbedChannelsDict["err"]:
                logger.error("getSubscribedChannelIDs returned err, skipping this cycle")
            else:
                subbedChannelIDs = subbedChannelsDict["list"]
                for channelID in subbedChannelIDs:
                    channelConfig = await redisConn.getChannelConfig(channelID)
                    channel = client.get_channel(channelID)
                    asyncio.create_task(safeSend(channel,text=Log2Text(Log,channelConfig)))
        else:
            await asyncio.sleep(BOT_LOOP_DELAY)




async def reaper(client):
    """
    Every $reaperInterval check for non-existant (dead) channels in subbedChannelIDs
    and remove them
    Essentially garbage collection for the channel list
    TODO: If parts of the Discord API goes down, this can sometimes trigger the
    removal of channels that do exist but Discord can't find them
    """
    await client.wait_until_ready()
    logger.info("Started")
    while not client.is_closed():
        subbedChannelsDict = await redisConn.getSubscribedChannelIDs()
        subbedChannelIDs = subbedChannelsDict["list"]
        for channelID in subbedChannelIDs:
            # Returns None if the channel ID does not exist OR the bot cannot "see" the channel
            if client.get_channel(channelID) == None:
                # No duplicate elements in the list so remove(value) will always work
                subbedChannelIDs.remove(channelID)
                logger.info(f"{channelID} is not a valid ID, removing from db")

        ret = await redisConn.safeSet("subscribedChannels", subbedChannelIDs, True)
        if not ret:
            logger.error(f"safeSet subscribedChannels failed, returned {ret}")

        await asyncio.sleep(REAPER_INTERVAL)

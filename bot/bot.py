#coding=utf-8
import discord
import re
from secure import DISCORD_TOKEN
from settings import *
from bot.modules.redisClient import startRedisConnection
redisConn=startRedisConnection()
from bot.modules import backgroundTasks
from bot.modules import errors
import logging
from bot.modules.discordUtils import safeSend
from bot.modules.utils import getDisplayName
logger = logging.getLogger(__name__)
logger.info("Starting bot")

class VRCBot(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.current_channel=None
        self.msg_level=4
    async def on_ready(self):
        if not await redisConn.exists("subscribedChannels"):
            await redisConn.safeSet("subscribedChannels", [], True)

        self.loop.create_task(backgroundTasks.notificationTask(self))
        self.loop.create_task(backgroundTasks.reaper(self))
        subbedChannelsDict = await redisConn.getSubscribedChannelIDs()
        totalSubbed = len(subbedChannelsDict["list"])
        totalGuilds = len(self.guilds)
        totalUsers = len(self.users)

        logger.info(f"Username: {self.user.name}")
        logger.info(f"ClientID: {self.user.id}")
        logger.info(f"Connected to {totalGuilds} guilds")
        logger.info(f"Connected to {totalSubbed} subscribed channels")
        logger.info(f"Serving {totalUsers} users")
        logger.info("Bot ready")

    async def on_message(self, message):
        if message.author == self.user:
            return
        #------------------------privilege judge-------------------------
        try:
            userIsManager = message.author.permissions_in(message.channel).manage_channels
        except AttributeError:
            # Happens if user has no roles
            userIsManager = False
        #------------------------privilege judge-------------------------

        message.content = message.content.lower()

        #-----------------------------------------------------addd channel-----------------------------------------------------
        if message.content.startswith(PREFIX + "addchannel"):
            if not userIsManager:
                replyMsg="You don't have permission to addchannel"
                return await safeSend(message.channel,text=replyMsg)
            # Add channel ID to subbed channels
            replyMsg = "This channel has been added to the launch notification service"
            await redisConn.setDefaultConfig(message.channel.id)
            subbedChannelsDict = await redisConn.getSubscribedChannelIDs()
            if subbedChannelsDict["err"]:
                # return here so nothing else is executed
                return await safeSend(message.channel, embed=errors.dbErrorEmbed)

            subbedChannelIDs = subbedChannelsDict["list"]
            if message.channel.id not in subbedChannelIDs:
                subbedChannelIDs.append(message.channel.id)
                ret = await redisConn.safeSet("subscribedChannels", subbedChannelIDs, True)
                if not ret:
                    return await safeSend(message.channel, embed=errors.dbErrorEmbed)
            else:
                replyMsg = "This channel is already subscribed to the launch notification service"

            await safeSend(message.channel, text=replyMsg)
        #-------------------------------------------------------remove channel--------------------------------------------------
        elif message.content.startswith(PREFIX + "removechannel"):
            if not userIsManager:
                replyMsg="You don't have permission to removechannel"
                return await safeSend(message.channel,text=replyMsg)
            # Remove channel ID from subbed channels
            replyMsg = "This channel has been removed from the launch notification service"

            subbedChannelsDict = await redisConn.getSubscribedChannelIDs()
            if subbedChannelsDict["err"]:
                # return here so nothing else is executed
                return await safeSend(message.channel, embed=errors.dbErrorEmbed)

            subbedChannelIDs = subbedChannelsDict["list"]
            try:
                # No duplicate elements in the list so remove(value) will always work
                subbedChannelIDs.remove(message.channel.id)
                ret = await redisConn.safeSet("subscribedChannels", subbedChannelIDs, True)
                if not ret:
                    return await safeSend(message.channel, embed=errors.dbErrorEmbed)
            except ValueError:
                replyMsg = "This channel was not previously subscribed to the launch notification service"

            await safeSend(message.channel, text=replyMsg)


        #-------------------------------------------addping------------------------------------------
        # Add/remove ping commands

        elif message.content.startswith(PREFIX + "add "):
            channelID = message.channel.id
            friendsToMetion=[f for f in message.content.split(" ")[1:] if not f.startswith("<@")]
            if "" in friendsToMetion:
                friendsToMetion.remove("")
            rolesToMention=re.findall('(<@!?\d+>)',message.content)
            if not rolesToMention:
                rolesToMention.append(message.author.mention)
            if not friendsToMetion:
                replyMsg = "Invalid input for add command"

            else:
                rolesToDisplay=await getDisplayName(self,rolesToMention)
                replyMsg = "Add friend(s) {} to mention {}".format(' '.join(friendsToMetion)," ".join(rolesToDisplay))
                new={}
                for f in friendsToMetion:
                    new[f]=rolesToMention

                channelConfig = await redisConn.getChannelConfig(channelID)
                mentions=channelConfig.get('mentions',{})
                mentions.update(new)
                channelConfig['mentions']=mentions
                ret =await redisConn.safeSet(REDIS_KEY_DISCORD_CHANNEL_CONFIG%message.channel.id,channelConfig,serialize=True)
                if not ret:
                    return await safeSend(message.channel, embed=errors.dbErrorEmbed)

            await safeSend(message.channel, text=replyMsg)

        elif message.content.startswith(PREFIX + "rm "):
            channelID = message.channel.id
            friendsToRemove = [f for f in message.content.split(" ")[1:] if not f.startswith("<@")]
            if "" in friendsToRemove:
                friendsToRemove.remove("")
            rolesToRemove = re.findall('(<@!?\d+>)', message.content)
            if not rolesToRemove:
                rolesToRemove.append(message.author.mention)
            if not friendsToRemove:
                replyMsg = "Invalid input for rm command"

            else:
                successed=[]
                keyNotExists=[]
                rolesNotExists=[]
                pop=[]
                channelConfig = await redisConn.getChannelConfig(channelID)
                try:
                    for f in friendsToRemove:
                        for r in rolesToRemove:
                            if f in channelConfig['mentions'].keys():
                                    if r in channelConfig['mentions'][f]:
                                        channelConfig['mentions'][f].remove(r)
                                        successed.append((f,r))
                                    else:
                                        if channelConfig['mentions'][f]==[]:
                                            channelConfig['mentions'].pop(f)
                                            pop.append(f)
                                        else:
                                            rolesNotExists.append((f,r))
                            else:
                                keyNotExists.append((f,r))

                    ret = await redisConn.safeSet(REDIS_KEY_DISCORD_CHANNEL_CONFIG % channelID, channelConfig, serialize=True)
                    if not ret:
                        return await safeSend(message.channel, embed=errors.dbErrorEmbed)
                    replyMsg =""
                    for f,r in successed:
                        replyMsg+=f"Successfully removed {f}'s mention for {r}.\n"
                    for f,r in keyNotExists:
                        replyMsg+=f"Failed to remove {f}'s mention for {r},no friends named {f}.\n"
                    for f,r in rolesNotExists:
                        replyMsg+=f"{f} has already removed for {r}.\n"
                    for f in pop:
                        replyMsg+=f"{f} has been deleted in config.\n"
                except TypeError and KeyError as e:
                     replyMsg = "An error occurred when removing mentions"
            await safeSend(message.channel, text=replyMsg)
        # -------------------------------------------end------------------------------------------

        elif userIsManager and message.content.startswith(PREFIX+"show"):

            if message.content.split(" ")[1]=="config":
                try:
                    map={}
                    config=await redisConn.getChannelConfig(message.channel.id)
                    for friend, roles in config['mentions'].items():
                        for mention in roles:
                            if mention not in map.keys():
                                ret=await getDisplayName(self,mention)
                                if ret:
                                    map[mention] =ret
                    config_text=str(config)
                    for id,displayName in map.items():
                        config_text=config_text.replace(id,displayName)
                    replyMsg="This channel's config is :\n"+config_text
                except Exception as e:
                    replyMsg="An error occurred when showing config"
                await safeSend(message.channel, text=replyMsg)

            if message.content.split(" ")[1] == "online":
                results=[]
                ret=await redisConn.scanAll(REDIS_KEY_UID.replace("%s","*"))
                if ret:
                    for key in ret:
                        User = await redisConn.safeGet(key, deserialize=True)
                        if User:
                            results.append(User)
                    onlines="\n".join([User.displayName for User in results])
                    replyMsg="Total Count {}:\n{}".format(len(ret),onlines)
                else:
                    replyMsg="An error occured when show online users"
                await safeSend(message.channel,text=replyMsg)


        elif userIsManager and message.content.startswith(PREFIX+"set"):

            channelID=message.channel.id
            channelConfig = await redisConn.getChannelConfig(channelID)
            key,value,*args=message.content.split(" ")[1:]

            try:
                if (key=="level" or key=="atlevel") and 0<=int(value)<=4:
                        channelConfig.update({key:int(value)})
                elif key=="verbose":
                        if value=="true":
                            channelConfig.update({key:True})
                        elif value=="false":
                            channelConfig.update({key:False})
                elif key=='mentions':
                    return await safeSend(message.channel, text="Please use !add command to set mentions")
                else:
                    return await safeSend(message.channel, text='No such configuration property.')

                replyMsg=f"set config {key}={value}"
                ret = await redisConn.safeSet(REDIS_KEY_DISCORD_CHANNEL_CONFIG % message.channel.id, channelConfig,
                                              serialize=True)
                if not ret:
                    return await safeSend(message.channel, embed=errors.dbErrorEmbed)
            except Exception as e:
                replyMsg="set command error"
            await safeSend(message.channel, text=replyMsg)
            
        elif userIsManager and message.content.startswith(PREFIX+"restore default"):
            replyMsg="This channel's configuration has been restored to default"
            ret=await redisConn.setDefaultConfig(message.channel.id)
            if not ret:
                return await safeSend(message.channel, embed=errors.dbErrorEmbed)
            await safeSend(message.channel, text=replyMsg)
if __name__ == '__main__':
    bot = VRCBot()
    bot.run(DISCORD_TOKEN)
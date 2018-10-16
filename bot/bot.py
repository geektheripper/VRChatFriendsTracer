import discord
from bot.modules.utils import priv
import re
from secure import DISCORD_TOKEN
from bot.modules import backgroundTasks

class VRCBot(discord.Client):
    current_channel=None
    msg_level=2
    async def on_ready(self):
        print('Logged in as')
        print(self.user.name)
        print(self.user.id)
        print('------')
        self.loop.create_task(backgroundTasks.notificationTask(self))
    async def on_message(self, message):
        if message.author == self.user:
            return
        if message.content.startswith('!start'):
             if self.current_channel==None:
                     await message.channel.send('开启上线提醒')
             elif self.current_channel!=message.channel:
                     await self.current_channel.send('关闭当前频道提醒')
                     await message.channel.send('在当前频道开启提醒')
             self.current_channel = message.channel
        elif message.content.startswith('!stop'):
            self.current_channel=None
            await message.channel.send('关闭上线提醒')
        elif message.content.startswith('!level'):
            try:
                if message.content == "!level":
                    pass
                else:
                    find=re.search("!level (\d)",message.content)
                    num=int(find.group(1))
                    if 1<=num<=4:
                        self.msg_level=num
                    else: await message.channel.send('请输入等级1-4')
                msg=','.join([i.split(".")[-1] for i in priv[self.msg_level]])
            except:
                await message.channel.send('处理命令出错')
            else:
                await message.channel.send('当前显示等级 %s'%msg)

import discord
from discord.ext import commands

class Test(commands.Cog):
    
    def __init__(self, bot: commands.Bot):
        self._bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.content.contains(':wink:'):
            channel = message.channel
            await channel.send(':wink:')

def setup(bot: commands.Bot):
    bot.add_cog(Test(bot))

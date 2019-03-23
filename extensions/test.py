import discord
from discord.ext import commands

import logging

import extensions.admin

class Test(commands.Cog):
    
    def __init__(self, bot: commands.Bot):
        self._bot = bot

    @commands.command()
    @extensions.admin.blacklisted([181181432989745152])
    async def test(self, ctx: commands.Context):
        await ctx.send('hello world')

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.content == ':wink:' or message.content == ':flushed:':
            channel = message.channel
            await channel.send(message.content)


def setup(bot: commands.Bot):
    bot.add_cog(Test(bot))

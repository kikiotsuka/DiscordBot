import discord
from discord.ext import commands

import logging, random

import extensions.admin

class Test(commands.Cog):
    
    def __init__(self, bot: commands.Bot):
        self._bot = bot

    @commands.command()
    @extensions.admin.blacklisted([181181432989745152])
    async def test(self, ctx: commands.Context):
        await ctx.send('hello world')

    @commands.command()
    @commands.is_owner()
    async def echo(Self, ctx: commands.Context):
        await  ctx.send('Hello world {}'.format(random.randint(0, 100)))

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        pass


def setup(bot: commands.Bot):
    bot.add_cog(Test(bot))

import discord
from discord.ext import commands

import logging

class Test(commands.Cog):
    
    def __init__(self, bot: commands.Bot):
        self._bot = bot

    @commands.command()
    @commands.is_owner()
    async def test(self, ctx: commands.Context):
        role = ctx.guild.get_role(557816089296502784)
        logging.info(role)
        await ctx.author.add_roles(role)
        await ctx.author.remove_roles(role)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.content == ':wink:' or message.content == ':flushed:':
            channel = message.channel
            await channel.send(message.content)


def setup(bot: commands.Bot):
    bot.add_cog(Test(bot))

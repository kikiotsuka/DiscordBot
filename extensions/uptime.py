import discord
from discord.ext import commands

import datetime

class Uptime(commands.Cog):
    
    def __init__(self, bot: commands.Bot):
        self._bot = bot
        self._start = datetime.datetime.now()

    @commands.command()
    def uptime(self, ctx: commands.Context):
        end = datetime.datetime.now()
        delta = end - self._start
        days, seconds = delta.days, delta.seconds
        minutes = seconds // 60
        seconds %= 60
        hours = minutes // 60
        minutes %= 60
        await ctx.send('Days: {}; Hours: {}; Minutes: {}; Seconds: {}'.format(days, hours, minutes, seconds))

def setup(bot: commands.Bot):
    logging.info('Setting up Uptime extension')
    bot.add_cog(Uptime(bot))
    logging.info('Done setting up uptime extension')

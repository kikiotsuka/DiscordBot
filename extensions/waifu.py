import discord
from discord.ext import commands

import logging, datetime
from collections import defaultdict

class Waifus(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self._bot = bot
        self._WAIFU_GACHA_CHANNEL_ID = 557963012472832021
        self._WAIFU_GACHA_CHANNEL = None
        self._WRONG_CHANNEL_MSG = 'You are rolling in the wrong channel {}!'
        self._REPORT_MSG = '{} just rolled in {}!'
        # heart reactions
        #'heart, cupid, two_hearts, heartpulse, heartbeat, sparkling_heart, hearts'

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if self._WAIFU_GACHA_CHANNEL is None:
            self._WAIFU_GACHA_CHANNEL = self._bot.get_channel(self._WAIFU_GACHA_CHANNEL_ID)
        if message.author.bot:
            pass
        else:
            if message.content.lower() in ['$w', '$h'] and message.channel.id != self._WAIFU_GACHA_CHANNEL:
                await message.channel.send(self._WRONG_CHANNEL_MSG.format(message.author.mention))
                await self._WAIFU_GACHA_CHANNEL.send(self._REPORT_MSG.format(message.author.mention,
                                                                             message.channel.mention))


def setup(bot: commands.Bot):
    logging.info('Setting up waifu extension')
    bot.add_cog(Waifus(bot))
    logging.info('Done setting up waifu extension')

import discord
from discord.ext import commands

import logging, datetime
from collections import defaultdict

class Waifus(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self._bot = bot
        self._users = set()
        self._animanga_rolls = defaultdict(int)
        self._game_rolls = defaultdict(int)
        self._closest_reset_time = self.closest_reset_time()
        self._WAIFU_GACHA_CHANNEL = 557963012472832021

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.content.lower() in ['$w', '$h'] and message.channel.id != self._WAIFU_GACHA_CHANNEL:
            await message.channel.send('You are rolling in the wrong channel {}!'.format(message.author.mention))
            gacha_channel = self._bot.get_channel(self._WAIFU_GACHA_CHANNEL)
            await gacha_channel.send('{} just rolled in the wrong channel!'.format(message.author.mention))

    '''
    @commands.Cog.listener():
    def on_message(self, message: discord.Message):
        if message.content.startswith('$') and message.author not in self._users:
            self._users.add(message.author)

        now = datetime.datetime.now()
        if datetime.datetime.now().minute == 26:
            self._animanga_rolls.clear()
            self._game_rolls.clear()

        if message.content.startswith('$wg') or message.content.startswith('$hg'):
            self._game_rolls[message.author] += 1
        elif message.content.startswith('$w') or message.content.startswith('$h'):
            self._animanga_rolls[message.author] += 1
        elif message.content.startswith('$rolls'):
            self._game_rolls[message.author] = 0
            self._animanga_rolls[message.author] = 0
    '''
        

    def closest_reset_time(self):
        '''
        Finds closest reset time that has passed.
        '''
        current_time = datetime.datetime.now()
        if current_time.minute >= 26:
            return datetime.time(hour=current_time.hour - current_time.hour % 3, minute=26)
        prev_hour = current_time.hour - 1 if current_time.hour > 0 else 24
        return datetime.time(hour=prev_hour - prev_hour % 3, minute=26)

def setup(bot: commands.Bot):
    logging.info('Setting up waifu extension')
    bot.add_cog(Waifus(bot))
    logging.info('Done setting up waifu extension')

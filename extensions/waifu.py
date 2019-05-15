import discord
from discord.ext import commands

import logging, datetime, pickle, os
from collections import defaultdict

class Waifus(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self._bot = bot
        self._WAIFU_GACHA_CHANNEL_ID = 557963012472832021
        self._WAIFU_GACHA_CHANNEL = None
        self._WRONG_CHANNEL_MSG = 'You should be rolling in {}, {}!'
        self._REPORT_MSG = '{} just rolled in {}!'
        # heart reactions
        # heart, cupid, two_hearts, heartpulse, heartbeat, sparkling_heart, hearts
        self._HEART_REACTIONS= [10084, 128152, 128149, 128151, 128147, 128150, 9829]
        # Track how many times the waifu should appear before auto-claiming
        self._MAX_APPEARANCES = 6
        # Track how often we should commit the data
        self._ROLL_THRESHOLD = 10
        # Tracks rolls for when to commit
        self._roll_counter = 0
        # Stores waifu roll counts for when bot restarts
        self._WAIFU_RECORDS_FILE = 'waifu.pickle'
        if os.path.isfile(self._WAIFU_RECORDS_FILE):
            logging.info('Successfully loaded waifu data')
            self._waifu_dict = pickle.load(open(self._WAIFU_RECORDS_FILE, 'rb'))
        else:
            logging.info('No waifu data found, initializing empty dictionary')
            self._waifu_dict = defaultdict(int)


    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if self._WAIFU_GACHA_CHANNEL is None:
            self._WAIFU_GACHA_CHANNEL = self._bot.get_channel(self._WAIFU_GACHA_CHANNEL_ID)

        if message.author.bot:
            if message.content.startswith(chr(128150)):
                waifu = message.content.split(r'**')[3]
                if waifu in self._waifu_dict:
                    del self._waifu_dict[waifu]
                    self._dump_records()
        else:
            if message.content.lower() in ['$w', '$h'] and message.channel != self._WAIFU_GACHA_CHANNEL:
                await message.channel.send(self._WRONG_CHANNEL_MSG.format(self._WAIFU_GACHA_CHANNEL.mention,
                                                                          message.author.mention))
                await self._WAIFU_GACHA_CHANNEL.send(self._REPORT_MSG.format(message.author.mention,
                                                                             message.channel.mention))


    @commands.Cog.listener()
    async def on_reaction_add(self, reaction: discord.Reaction, member: discord.Member):
        if reaction.message.channel == self._WAIFU_GACHA_CHANNEL and \
           not reaction.custom_emoji and \
           ord(reaction.emoji) in self._HEART_REACTIONS:
            waifu = reaction.message.embeds[0].author.name
            self._waifu_dict[waifu] += 1
            if self._waifu_dict[waifu] >= self._MAX_APPEARANCES:
                await reaction.message.channel.send('Claiming {} because nobody wants this trash'.format(waifu))
                await reaction.message.add_reaction(reaction)
            self._roll_counter += 1
            if self._roll_counter >= self._ROLL_THRESHOLD:
                self._roll_counter = 0
                self._dump_records()


    def _dump_records(self):
        logging.info('Dumping data')
        with open(self._WAIFU_RECORDS_FILE, 'wb') as f:
            pickle.dump(self._waifu_dict, f)


def setup(bot: commands.Bot):
    logging.info('Setting up waifu extension')
    bot.add_cog(Waifus(bot))
    logging.info('Done setting up waifu extension')

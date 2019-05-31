import discord
from discord.ext import commands

import logging, os

class Audio(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self._bot = bot
        self._AUDIO_DIR = 'audio/'


    @commands.command()
    async def plist(self, ctx: commands.Context):
        l = ', '.join(filter(lambda x: x.endswith('.mp3'), os.listdir(self._AUDIO_DIR)))
        await ctx.send('`{}`'.format(l))

    @commands.command(aliases=['p'])
    async def play(self, ctx: commands.Context, fname: str='tuturuu.mp3'):
        await ctx.message.delete()
        vc = await self._get_ch(ctx.guild, ctx.author.voice.channel)

        if vc is None:
            await ctx.send('You need to be in a channel for me to work')

        if not fname.endswith('.mp3'):
            fname += '.mp3'

        fname = self._AUDIO_DIR + fname
        if os.path.isfile(fname):
            source = discord.FFmpegPCMAudio(fname)
            if not vc.is_playing():
                vc.play(source)
            else:
                vc.source = source
        else:
            await ctx.send('{} doesn\'t exist!'.format(fname), delete_after=1.5)

    async def _get_ch(self, guild: discord.Guild, channel: discord.VoiceChannel):
        if self._bot.voice_clients:
            for ch in self._bot.voice_clients:
                if ch.guild == guild:
                    if ch.channel == channel or channel is None:
                        logging.info('Already in channel')
                        return ch
                    if channel is not None:
                        logging.info('Moving channels')
                        ch.disconnect()
        if channel is not None:
            logging.info('Joining channel')
            return await channel.connect()
        logging.info('Caller is not in a channel')
        return None

def setup(bot: commands.Bot):
    bot.add_cog(Audio(bot))

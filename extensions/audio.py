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

    @commands.command(description='If the bot does not come into the channel use me')
    async def preset(self, ctx: commands.Context):
        if ctx.guild.voice_client is not None:
            await ctx.guild.voice_client.disconnect()
        await ctx.send('Reset the internal state')

    @commands.command(aliases=['p'])
    async def play(self, ctx: commands.Context, fname: str='tuturuu.mp3'):
        await ctx.message.delete()
        
        vc_ch = ctx.author.voice.channel if ctx.author.voice is not None else None
        vc = await self._get_ch(ctx.guild, vc_ch)

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
        if channel is not None:
            if guild.voice_client is not None and guild.voice_client.is_connected():
                if guild.voice_client.channel == channel:
                    return guild.voice_client
                await guild.voice_client.disconnect()
            return await channel.connect()
        
        if guild.voice_client is not None:
            return guild.voice_client
        return None

def setup(bot: commands.Bot):
    bot.add_cog(Audio(bot))

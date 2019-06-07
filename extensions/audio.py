import discord
from discord.ext import commands

import logging, os, collections, pickle, typing

class Audio(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self._bot = bot
        self._AUDIO_DIR = 'audio/'
        self._MAP_FILE = self._AUDIO_DIR + 'whois.pickle'
        self._whois = self._map_audio()

    def _map_audio(self):
        if os.path.isfile(self._MAP_FILE):
            return pickle.load(open(self._MAP_FILE, 'rb'))
        return collections.defaultdict(list)

    def _update_map_audio(self):
        with open(self._MAP_FILE, 'wb') as f:
            pickle.dump(self._whois, f)

    @commands.command()
    @commands.is_owner()
    async def pchangekey(self, ctx: commands.Context, *args):
        if len(args) != 2:
            await ctx.send('Usage: <old key> <new key>')
        else:
            if args[0] in self._whois:
                self._whois[args[1]] = self._whois.pop(args[0])
                self._update_map_audio()
                await ctx.send('Updated dictionary key from {} to {}'.format(args[0], args[1]))
            else:
                await ctx.send('Error: old key not found, see `plist -u` for key list')

    @commands.command()
    @commands.is_owner()
    async def padd(self, ctx: commands.Context, owner: str='', *args):
        newkey = '--new' in args
        overwrite = '--overwrite' in args

        if not owner:
            await ctx.send('Error, needs an owner name')
            return

        # Check if new key should be added
        if owner not in self._whois.keys() and not newkey:
            await ctx.send('Error, that key does not exist. Use `--new` for adding a new key')
            return

        # Grab audio file
        audio_file = ctx.message.attachments[0] if ctx.message.attachments else None
        if audio_file is not None and audio_file.filename.endswith('.mp3'):
            # Check if file exists or not
            if not overwrite:
                for files in self._whois.values():
                    if audio_file.filename[:-4] in files:
                        await ctx.send('Error, file already exists. Use `--overwrite` to overwrite file')
                        return

            await audio_file.save(self._AUDIO_DIR + audio_file.filename)
            self._whois[owner].append(audio_file.filename[:-4])
            self._whois[owner].sort()
            self._update_map_audio()
            await ctx.send('Added file to the audio index')
        else:
            await ctx.send('Error, missing audio file')

    @commands.command()
    async def plist(self, ctx: commands.Context, arg: typing.Optional[str]):
        data = '```'
        if arg and arg == '-u':
            for key in sorted(self._whois.keys()):
                data += '{} -> {} entries\n'.format(key, len(self._whois[key]))
        else:
            for key in sorted(self._whois.keys()):
                data += '{}:\n\t{}\n'.format(key, ', '.join(self._whois[key]))
        data += '```'
        await ctx.send(data)

    @commands.command(help='If the bot does not come into the channel use me')
    async def preset(self, ctx: commands.Context):
        if ctx.guild.voice_client is not None:
            await ctx.guild.voice_client.disconnect()
        await ctx.send('Reset the internal state')

    @commands.command(aliases=['p'])
    async def play(self, ctx: commands.Context, fname: str='hellomakise.mp3'):
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

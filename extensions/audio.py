import discord
from discord.ext import commands, tasks

import logging, os, collections, pickle, typing, datetime, time, asyncio

DELAY_TIME = 10

class Audio(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self._bot = bot
        self._AUDIO_DIR = 'audio/'
        self._MAP_FILE = self._AUDIO_DIR + 'whois.pickle'
        self._whois = self._map_audio()
        self._last = dict()
        self._ping_ch_id = [384226521000312852, 714249564852322396]
        self._ping_ch = None
        self._task = None

    def _map_audio(self):
        if os.path.isfile(self._MAP_FILE):
            return pickle.load(open(self._MAP_FILE, 'rb'))
        return collections.defaultdict(list)

    def _update_map_audio(self):
        with open(self._MAP_FILE, 'wb') as f:
            pickle.dump(self._whois, f)

    async def cog_before_invoke(self, ctx: commands.Context):
        self._last[ctx.guild.id] = datetime.datetime.now() 

    async def cog_after_invoke(self, ctx: commands.Context):
        if not self.auto_disconnect.get_task():
            logging.info('Starting repeat looper')
            self.auto_disconnect.start()

    @tasks.loop(minutes=DELAY_TIME)
    async def auto_disconnect(self):
        logging.info('Checking auto disconnect')
        for gid, last in self._last.items():
            # Time delta in minutes
            dt = (datetime.datetime.now() - last).seconds / 60
            logging.info('guild: {}; time since: {}'.format(gid, dt))
            if dt >= DELAY_TIME:
                logging.info('Attempting to auto disconnect')
                guild = self._bot.get_guild(gid)
                if guild.voice_client is not None:
                    logging.info('Killing background process')
                    await guild.voice_client.disconnect()
                    self.auto_disconnect.stop()

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
            if audio_file.filename[:-4] not in self._whois[owner]:
                self._whois[owner].append(audio_file.filename[:-4])
                self._whois[owner].sort()
                self._update_map_audio()
            await ctx.send('Added or updated audio index file')
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
        if vc_ch is None:
            await ctx.send('You need to be in a channel for me to work')

        if not fname.endswith('.mp3'):
            fname += '.mp3'

        fname = self._AUDIO_DIR + fname
        if os.path.isfile(fname):
            voice = ctx.guild.voice_client
            if voice is None:
                voice = await vc_ch.connect()

            source = discord.FFmpegPCMAudio(fname)
            if not voice.is_playing():
                voice.play(source)
            else:
                voice.source = source
            await self._delay_remove(voice)
        else:
            await ctx.send('{} doesn\'t exist!'.format(fname), delete_after=1.5)

    async def _delay_remove(self, voice):
        if self._task is not None:
            self._task.cancel()
        loop = asyncio.get_event_loop()
        self._task = loop.create_task(self._delay_remove_helper(voice))

    async def _delay_remove_helper(self, voice):
        try:
            await asyncio.sleep(15)
            await voice.disconnect()
        except asyncio.CancelledError:
            pass

    @commands.command()
    async def ping(self, ctx: commands.Context, member: discord.Member):
        curr_ch = member.voice.channel
        if self._ping_ch is None:
            self._ping_ch = [ctx.guild.get_channel(ch_id) for ch_id  in self._ping_ch_id]
        if curr_ch is not None:
            await ctx.send('Pinging {}'.format(member.mention))
            for i in range(6):
                await member.move_to(self._ping_ch[i % 2], reason='Pinging')
                time.sleep(0.2)
            await member.move_to(curr_ch, reason='Pinging')
        else:
            await ctx.send('{} is not in a voice channel'.format(member.mention))

def setup(bot: commands.Bot):
    bot.add_cog(Audio(bot))

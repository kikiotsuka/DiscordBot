import discord
from discord.ext import commands
import pdb

class Admin():

    def __init__(self, bot: commands.Bot):
        self._bot = bot
        self._blacklisted_users = []
        self._extensions = []

    @commands.command()
    @commands.is_owner()
    async def reload(self, ctx: commands.Context, *elist: (str)):
        if not elist:
            elist = self._extensions

        if elist:
            # Extensions that succeded or failed to load
            success = []
            failed = []

            for extension in elist:
                if not extension.startswith('extensions'):
                    extension = 'extensions.' + extension
                if extension in self._bot.extensions:
                    self._bot.unload_extension(extension)
                try:
                    self._bot.load_extension(extension)
                    success.append(extension)
                except Exception as e:
                    failed.append(extension)
                    print(e)

            if success:
                await ctx.send('Successfully loaded: `{}`'.format(success))
            if failed:
                await ctx.send('Failed to load: `{}`, see console for more details'.format(failed))
        else:
            await ctx.send('Extensions list is empty')

    @commands.command()
    @commands.is_owner()
    async def load(self, ctx: commands.Context, *elist: (str)):
        if not elist:
            await ctx.send('Error: expected list of extensions')
        else:
            await ctx.invoke(self.reload, *elist)

    @commands.command()
    @commands.is_owner()
    async def unload(self, ctx: commands.Context, *elist: (str)):
        if not elist:
            await ctx.send('Error: expected list of extensions')
        else:
            success = []
            failed = []
            for extension in elist:
                if extension == 'admin':
                    await ctx.send('Can\'t unload admin extension')
                else:
                    if not extension.startswith('extensions'):
                        extension = 'extensions.' + extension
                    if extension in self._bot.extensions:
                        success = True
                        self._bot.unload_extension(extension)
                    else:
                        failed.append(extension)

            if success:
                await ctx.send('Successfully unloaded: `{}`'.format(success))
            if failed:
                await ctx.send('Failed to unload: `{}`, see console for more details'.format(failed))

    @commands.command()
    @commands.is_owner()
    async def list_extensions(self, ctx: commands.Context):
        await ctx.send('`Extensions: {}`'.format(list(self._bot.extensions.keys())))


def setup(bot):
    print('Setting up Admin extension')
    bot.add_cog(Admin(bot))

import discord
from discord.ext import commands

class Admin(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self._bot = bot

    @commands.command()
    @commands.is_owner()
    async def reload(self, ctx: commands.Context, *extension_list: (str)):
        if not extension_list:
            extension_list = self._bot.extensions.copy().keys()

        if extension_list:
            # Extensions that succeded or failed to load
            success = []
            failed = []

            for extension in self._preprocess_extensions(extension_list):
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
    async def load(self, ctx: commands.Context, *extension_list: (str)):
        if not extension_list:
            await ctx.send('Error: expected list of extensions')
        else:
            await ctx.invoke(self.reload, *extension_list)

    @commands.command()
    @commands.is_owner()
    async def unload(self, ctx: commands.Context, *extension_list: (str)):
        if not extension_list:
            await ctx.send('Error: expected list of extensions')
        else:
            success = []
            failed = []
            for extension in self._preprocess_extensions(extension_list):
                if extension == 'admin':
                    await ctx.send('Can\'t unload admin extension')
                else:
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

    async def on_command_error(self, ctx, error):
        error = getattr(error, 'original', error)

        ignored = (commands.CommandNotFound, commands.UserInputError)

        if isinstance(error, ignored):
            return
        elif isinstance(error, commands.NotOwner):
            await ctx.send('You need to be a bot owner to run this command')
        else:
            await ctx.send('Fatal error occured in Admin extension, see console')

    def _preprocess_extensions(self, extension_list):
        for extension in extension_list:
            if not extension.startswith('extensions'):
                yield 'extensions.' + extension
            else:
                yield extension


def setup(bot: commands.Bot):
    print('Setting up Admin extension')
    bot.add_cog(Admin(bot))

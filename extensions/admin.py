import discord
from discord.ext import commands

import logging

class Admin(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self._bot = bot
        self._initial_extensions = [
            'extensions.misc',
            'extensions.uptime'
        ]

        for extension in self._initial_extensions:
            if extension not in self._bot.extensions:
                self._bot.load_extension(extension)

    @commands.command()
    @commands.is_owner()
    async def shutdown(self, ctx: commands.Context):
        await ctx.send('Goodbye')
        await self._bot.logout()

    @commands.command()
    @commands.is_owner()
    async def reload(self, ctx: commands.Context, *extension_list: (str)):
        if not extension_list:
            extension_list = set(self._bot.extensions.keys())

        # Extensions that succeded or failed to load
        success = []
        failed = []

        for extension in self._preprocess_extensions(extension_list):
            try:
                if extension in self._bot.extensions:
                    self._bot.reload_extension(extension)
                else:
                    self._bot.load_extension(extension)
                success.append(extension)
            except Exception as e:
                failed.append(extension)
                print(e)

        if success:
            await ctx.send('Successfully loaded: `{}`'.format(success))
        if failed:
            await ctx.send('Failed to load: `{}`, see console for more details'.format(failed))

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
        if hasattr(ctx.command, 'on_error'):
            return

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
    logging.info('Setting up Admin extension')
    bot.add_cog(Admin(bot))
    logging.info('Done setting up Admin extension')


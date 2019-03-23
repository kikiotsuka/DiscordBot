import discord
from discord.ext import commands

import logging, traceback, typing, datetime

# Global settings
whitelist = [
    141102297550684160
]

blacklist = [
    126485504114950144
]

# Checks decorator
def whitelisted(local_whitelist=None):
    if local_whitelist is None:
        local_whitelist = []

    async def perm_predicate(ctx: commands.Context):
        return ctx.author.id in whitelist or ctx.author.id in local_whitelist
    return commands.check(perm_predicate)

def blacklisted(local_blacklist=None):
    if local_blacklist is None:
        local_blacklist = []

    async def perm_predicate(ctx: commands.Context):
        return not ctx.author.id in blacklist and not ctx.author.id in local_blacklist
    return commands.check(perm_predicate)

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
    async def cleanup(self, ctx: commands.Context, target: typing.Optional[discord.Member]=None, number: int=1):
        if not 1 <= number <= 100:
            await ctx.send('Error: Expected a number in the range [1, 100]')
            return
        # If the user is invoking it on themselves, don't remove the calling command
        skip_first = False
        if target is None or target == ctx.author:
            skip_first = True
            target = ctx.author

        to_remove = []
        async for message in ctx.channel.history(limit=200):
            time_delta = datetime.datetime.now() - message.created_at
            # Cannot remove messages older than 14 days
            if time_delta.days > 14:
                break

            if message.author == target:
                if skip_first:
                    skip_first = False
                    continue
                to_remove.append(message)

                if len(to_remove) >= number:
                    break

        if to_remove:
            await ctx.channel.delete_messages(to_remove)
            await ctx.send('Successfully deleted {} messages'.format(len(to_remove)))
        else:
            await ctx.send('Could not find any messages to delete')

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
                logging.info(e)
                traceback.print_exc()

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


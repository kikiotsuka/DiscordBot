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
            'extensions.uptime',
            'extensions.waifu'
        ]

        for extension in self._initial_extensions:
            if extension not in self._bot.extensions:
                self._bot.load_extension(extension)

    @commands.command()
    async def cleanup(self,
                      ctx: commands.Context,
                      target: typing.Optional[discord.Member]=None,
                      delete_count: int=1):
        if not 1 <= delete_count <= 100:
            await ctx.send('Error: Expected a number in the range [1, 100]')
            return
        if target is None or target == ctx.author:
            target = ctx.author

        def predicate(member: discord.Member):
            return member == target
        await self._cleanup_aux(ctx, delete_count, predicate)

    @commands.command()
    @whitelisted([130891181922975744, 181181432989745152])
    async def purge(self, ctx: commands.Context, deletion_value: int=1, silent: bool=True):
        # Rough estimate
        if len(str(deletion_value)) > 15:
            message_id = deletion_value
            delete_count = 100
            # Alternative exit condition
            def exit_predicate(curr_id: int):
                return message_id == curr_id
        elif deletion_value <= 100:
            message_id = None
            delete_count = deletion_value
        else:
            await ctx.send('Cannot delete more than 100 messages')
            return

        def predicate(member: discord.Member):
            return True
        exit_predicate = None

        await self._cleanup_aux(ctx, delete_count + 1, predicate, exit_predicate)

    async def _cleanup_aux(self,
                           ctx: commands.Context,
                           delete_count: int,
                           predicate: typing.Callable[[discord.Member], bool],
                           exit_predicate: typing.Callable[[discord.Message], bool]=None):
        to_remove = []
        exit_cond = True if exit_predicate is None else False

        delete_invoking_command = True
        async for message in ctx.channel.history(limit=100):
            time_delta = datetime.datetime.now() - message.created_at
            # Cannot remove messages older than 14 days
            if time_delta.days >= 14:
                break

            if delete_invoking_command and message.content[1:] in ['cleanup', 'purge']:
                to_remove.append(message)
                delete_invoking_command = False
                continue

            if predicate(message.author):
                to_remove.append(message)

                # +1 to include the invoking command
                if len(to_remove) >= delete_count:
                    break

            if exit_predicate is not None and exit_predicate(message.id):
                exit_cond = True
                break
        
        if exit_cond and to_remove:
            await ctx.channel.delete_messages(to_remove)
            status_message = 'Successfully deleted {} messages (including the invoking command)'
            await ctx.send(status_message.format(len(to_remove)), delete_after=5.0)
        else:
            await ctx.send('Could not find any messages to delete', delete_after=5.0)


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


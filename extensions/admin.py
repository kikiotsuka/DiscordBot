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
            'extensions.waifu',
            'extensions.audio'
        ]

        for extension in self._initial_extensions:
            if extension not in self._bot.extensions:
                self._bot.load_extension(extension)

    @commands.Cog.listener()
    async def on_guild_role_update(self, before: discord.Role, after: discord.Role):
        immutable = 419778682081771525
        
        async for entry in before.guild.audit_logs(limit=5, action=discord.AuditLogAction.role_update):
            print(entry.user.bot, entry.target, before.id)
            if not entry.user.bot and entry.target.id == before.id:
                if before.id == immutable:
                    await after.edit(name=before.name,
                                     permissions=before.permissions,
                                     color=before.color)
                    logging.info('Revert: {}: {}, {}: {}, {}: {}, {}: {}, {}: {}'.format(
                        after.name, before.name,
                        after.permissions, before.permissions,
                        after.color, before.color))
                    break

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
    async def create_role(self, ctx: commands.Context):
        message = ctx.message
        role_name = ' '.join(filter(lambda x: not x.startswith('<@!'), message.content.strip().split()[1:]))
        if role_name:
            role = None
            try:
                role = await ctx.guild.create_role(
                    name=role_name,
                    color=discord.Color.blue(),
                    mentionable=True,
                    reason='role made by {}'.format(ctx.author.name))
            except Exception as e:
                logging.error(e)
                await ctx.send('Failed to make that role')

            if role is not None:
                failed = []
                for member in set(message.mentions):
                    try:
                        roles = member.roles + [role]
                        await member.edit(roles=roles)
                    except Exception as e:
                        logging.error(e)
                        failed.append(member)
                await ctx.send('Successfully Created role {}'.format(role.mention))
                if failed:
                    await ctx.send('Could not add {} to the role'.format(', '.join(
                        map(lambda x: x.mention, failed))))
        else:
            await ctx.send('You did not specify the name of the role')

    @commands.command(help='Adds (or removes if the --remove flag is used) the mentioned people to the role')
    async def update_role(self, ctx: commands.Context):
        add = '--remove' not in ctx.message.content
        members = ctx.message.mentions
        if not ctx.message.role_mentions:
            await ctx.send('You did not specify a role')
            return
        if len(ctx.message.role_mentions) > 1:
            await ctx.send('You are allowed to only update one role at a time')
            return
        if not members:
            await ctx.send('You did not specify anyone to update their roles')
            return
        role = ctx.message.role_mentions[0]
        successful = []
        failed = []
        for member in members:
            roles = member.roles
            if add:
                if role not in roles:
                    roles.append(role)
                    await member.edit(roles=roles)
                    successful.append(member)
                else:
                    failed.append(member)
            else:
                if role in roles:
                    roles.remove(role)
                    await member.edit(roles=roles)
                    successful.append(member)
                else:
                    failed.append(member)
        if successful:
            await ctx.send('Successfully {} {} {} the role'.format('added' if add else 'removed',', '.join(
                map(lambda x: x.mention, successful)), 'to' if add else 'from'))
        if failed:
            if add:
                await ctx.send('Failed to add {} to the role, they are already part of it'.format(', '.join(
                    map(lambda x: x.mention, failed))))
            else:
                await ctx.send('Failed to remove {} from the role, they were not a part of it'.format(', '.join(
                    map(lambda x: x.mention, failed))))

    @commands.command()
    @whitelisted([130891181922975744, 181181432989745152])
    async def purge(self, ctx: commands.Context, deletion_value: int=1):
        delete_count, exit_predicate = self._stop_predicate(deletion_value)
        if delete_count == -1:
            await ctx.send('Cannot delete more than 100 messages')
            return

        def predicate(member: discord.Member):
            return True

        await self._cleanup_aux(ctx, delete_count, predicate, exit_predicate)

    def _stop_predicate(self, deletion_value: int):
        if len(str(deletion_value)) > 15:
            def exit_predicate(curr_id: int):
                return deletion_value == curr_id
            return 100, exit_predicate
        if deletion_value > 100:
            return -1, None
        return deletion_value, None

    async def _cleanup_aux(self,
                           ctx: commands.Context,
                           delete_count: int,
                           predicate: typing.Callable[[discord.Member], bool],
                           exit_predicate: typing.Callable[[discord.Message], bool]=None):
        to_remove = []
        err_msg = 'Could not find any messages to delete'
        exit_cond = True if exit_predicate is None else False

        async for message in ctx.channel.history(limit=100):
            time_delta = datetime.datetime.now() - message.created_at
            # Cannot remove messages older than 14 days
            if time_delta.days >= 14:
                err_msg = 'You can\'t delete messages older than 14 days'
                break

            if message.id == ctx.message.id:
                to_remove.append(message)
                continue

            if predicate(message.author):
                to_remove.append(message)

                # +1 to include the invoking command
                if len(to_remove) > delete_count:
                    break

            if exit_predicate is not None and exit_predicate(message.id):
                exit_cond = True
                break
        
        # Check len > 1 because it deletes the invoking command
        if exit_cond and len(to_remove) > 1:
            await ctx.channel.delete_messages(to_remove)
            status_message = 'Successfully deleted {} messages (including the invoking command)'
            await ctx.send(status_message.format(len(to_remove)), delete_after=5.0)
        else:
            await ctx.send(err_msg, delete_after=5.0)


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


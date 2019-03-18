import discord
from discord.ext import commands

import os, random, re, typing, traceback, logging

class Misc(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self._bot = bot
        self._res_path = 'res/'
        self._spongebob_regex = re.compile(r'<@!?(\d+)>|<@&(\d+)>|<#(\d+)>')

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error: discord.DiscordException):
        logging.debug('Misc error by {}: {}'.format(ctx.author, error))
        ignored = (commands.CommandNotFound)
        error = getattr(error, 'original', error)

        if isinstance(error, ignored):
            return

        if await self._bot.is_owner(ctx.author):
            traceback.print_exc()
            await ctx.send('You messed up, but I forgive you {}'.format(ctx.author.mention))
            return

        if isinstance(error, commands.NotOwner):
            await ctx.invoke(self.disobedience, ctx.author, 'treason with the power of a trillion suns')
        elif isinstance(error, commands.CommandOnCooldown):
            await ctx.invoke(self.disobedience, ctx.author, 'spamming a command')
        elif isinstance(error, commands.UserInputError):
            await ctx.invoke(self.disobedience, ctx.author, 'incompetence')
        else:
            logging.error('Something fatal ocurred')

    @commands.command()
    async def spongecase(self,
                   ctx: commands.Context,
                   member: typing.Optional[discord.Member]=None,
                   distance: typing.Optional[int]=0,
                   *,
                   message=None):
        logging.info('Spongecase {} {} {}'.format(member, distance, message))
        if message is not None:
            # Prevent boring messages
            spongecased_message = self._spongecaseify(message)
            while spongecased_message.isupper() or spongecased_message.islower():
                spongecased_message = self._spongecaseify(message)

            spongecased_being = member if member is not None else ctx.author
            await ctx.send('{}: {}'.format(spongecased_being.mention, self._spongecaseify(message)))
        elif member is not None:
            await ctx.invoke(self.spongecase_last_message, member, distance)
        else:
            await ctx.invoke(self.disobedience, ctx.author, 'incompetence')
        logging.info('Done spongecase')

    @commands.command(hidden=True)
    async def spongecase_last_message(self, ctx: commands.Context, member: discord.Member, distance: int):
        message_count = 0
        async for message in ctx.channel.history(limit=200):
            if message.author == member:
                if message_count >= distance:
                    await ctx.invoke(self.spongecase, member=member, message=message.content)
                    break
                else:
                    message_count += 1
        else:
            await ctx.invoke(self.disobedience, ctx.author, 'incompetence')

    @commands.command(aliases=['dildo', 'whale'])
    async def trout(self, ctx: commands.Context, member: discord.Member):
        logging.info('Trout {} by {}'.format(member, ctx.author))
        await ctx.message.delete()
        if await self._bot.is_owner(member) or member.bot:
            await ctx.invoke(self.disobedience, member, 'disobedience')
        else:
            if ctx.invoked_with in ['trout']:
                await ctx.send('{} gets slapped in the face with a {}'.format(member.mention, ctx.invoked_with))
            elif ctx.invoked_with in ['dildo']:
                await ctx.send('{} gets a {} shoved up their ass'.format(member.mention, ctx.invoked_with))
            elif ctx.invoked_with in ['whale']:
                await ctx.send('{} gets smushed by a giant {}'.format(member.mention, ctx.invoked_with))
        logging.info('Done trouting')

    # Owner only commands

    @commands.command()
    @commands.is_owner()
    async def smite(self, ctx: commands.Context, member: discord.Member):
        logging.info('Smite {}'.format(member))
        await ctx.message.delete()
        await ctx.invoke(self.disobedience, member, 'it was the way of the Steins;Gate')

    @commands.command()
    @commands.is_owner()
    async def disobedience(self, ctx: commands.Context, member: discord.Member, reason: str):
        await ctx.send('{} smites {} for {}'.format(self._bot.user.mention, member.mention, reason))

    # Listeners

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        logging.info('Author: {}; Content: {}'.format(message.author, message.content))
        # Ignore anything from a bot
        if message.author.bot:
            return

        channel = message.channel
        # Get mad
        if message.mention_everyone:
            file_list = os.listdir(self._res_path)
            selected_reaction = random.choice(file_list)
            condemn = '{} is BANISHED to the shadow realm'.format(message.author.mention)
            await channel.send(content=condemn, file=discord.File(self._res_path + selected_reaction))

    # Helper methods
    def _spongecaseify(self, message):
        tokens = message.split(' ')
        response_words = [tokens[0]]
        for word in tokens[1:]:
            spongbobified = ''
            if not self._spongebob_regex.search(word):
                for c in word:
                    spongbobified += c.upper() if random.random() < 0.5 else c.lower()
                response_words.append(spongbobified)
            else:
                response_words.append(word)
        return ' '.join(response_words)

def setup(bot: commands.Bot):
    logging.info('Setting up Misc extension')
    bot.add_cog(Misc(bot))
    logging.info('Done setting up Misc extension')

#!/usr/bin/env python3

import discord
from discord.ext import commands

import sys

# Constants
AUTH_FILE = 'auth.json'
AUTH_FIELD = 'token'

COMMAND_PREFIX = '?'

BOT_OWNER = 141102297550684160
BOT_DESCRIPTION = 'Bot for personal use with random commands'

# Extensions to load
extensions = []

bot = commands.Bot(command_prefix=COMMAND_PREFIX, description=BOT_DESCRIPTION)

@bot.event
async def on_ready():
    print('Bot is ready')

@bot.command(checks=is_owner, hidden=True)
async def reload(elist=None):
    '''
    Reloads extensions
    '''
    if elist is None:
        elist = extensions

    # Extensions that succeded or failed to load
    success = []
    failed = []

    for extension in elist:
        bot.unload_extension(extension)
        try:
            bot.load_extension(extension)
            success.append(extension)
        except Exception as e:
            failed.append(extension)
            print(e)

    await bot.say('Successfully loaded: {}'.format(success))
    await bot.say('Failed to load: {}, see console for more details'.format(failed))

#!/usr/bin/env python3

import discord
from discord.ext import commands

import sys, json, traceback, logging

# Constants
AUTH_FILE = 'auth.json'
AUTH_FIELD = 'token'

EXTENSION_ADMIN = 'extensions.admin'

COMMAND_PREFIX = '?'

BOT_DESCRIPTION = 'Bot for personal use with random commands'

bot = commands.Bot(command_prefix=COMMAND_PREFIX, description=BOT_DESCRIPTION)

# Setup logging
logging.getLogger().setLevel(logging.INFO)
logging.basicConfig(stream=sys.stdout)

@bot.event
async def on_ready():
    logging.info('Bot is ready')

@bot.event
async def on_command_error(ctx: commands.Context, error: discord.DiscordException):
    # Ignore invalid commands
    if isinstance(error, commands.CommandNotFound):
        return
    # Propogate error
    raise error

def __main__():
    bot_token = json.load(open(AUTH_FILE, 'r'))[AUTH_FIELD]
    if load_extension(EXTENSION_ADMIN):
        bot.run(bot_token)
    else:
        print('Failed to load admin extension')

def load_extension(extension_name: str):
    try:
        bot.load_extension(extension_name)
    except Exception as e:
        traceback.print_exc()
        return False
    return True

if __name__ == '__main__':
    __main__()

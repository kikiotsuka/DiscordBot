#!/usr/bin/env python3

import discord
from discord.ext import commands

import sys, json, traceback

# Constants
AUTH_FILE = 'auth.json'
AUTH_FIELD = 'token'

COMMAND_PREFIX = '?'

BOT_DESCRIPTION = 'Bot for personal use with random commands'

bot = commands.Bot(command_prefix=COMMAND_PREFIX, description=BOT_DESCRIPTION)

@bot.event
async def on_ready():
    print('Bot is ready')

def __main__():
    bot_token = json.load(open(AUTH_FILE, 'r'))[AUTH_FIELD]
    if load_admin_extension():
        bot.run(bot_token)
    else:
        print('Failed to load admin extension')

def load_admin_extension():
    try:
        bot.load_extension('extensions.admin')
    except Exception as e:
        traceback.print_exc()
        return False
    return True

if __name__ == '__main__':
    __main__()

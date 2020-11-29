# bot-main.py
""" discord-among-us

This bot is meant to handle a private Among Us game, with several dozen running concurrently.

I like the idea of making this stateless, so no database needed here. Everything should be stored in Discord.

I'm thinking about setting this up so there's a text channel created for every voice channel, and is private for that voice channel (i.e. no one else can see it)

The main purpose here is to allow for a party to join a group, join their private match via the game code (shared through a text channel) and play with voice chat.

Things like setting player limits and creating an auto-join system with categories will come later. Maybe you want 5-6 friends to play together, or only want to join non-nsfw channels.

Thoughts on the auto join system:
Creating private lobbies
Roles - language-specific filters (only German / only english)


"""

import os
import logging
from systemd.journal import JournalHandler

from dotenv import load_dotenv
from discord.ext import commands
from discord import utils
import discord

from src.common import Common
import src.self_roles as self_roles
import src.server_stats as server_stats
import src.admin_logging as admin_logging
import src.server_rules as server_rules
import src.admin_commands as admin_commands
import src.lobby_commands as lobby_commands
import src.lobby_handler as lobby_handler
import src.start_here as start_here


class debug_logger:
    # Logger meant for debugging at the terminal.

    level = 0

    def handle(self, record):
        self.emit(record)

    def handleError(self, record):
        self.emit(record)

    def emit(self, record):
        # https://docs.python.org/3/library/logging.html#logrecord-objects
        # Extracts the log message for terminal printing
        # Formatting: filename, line_number, message
        msg = f"{record.pathname}, {record.lineno}, \"{record.msg}\""
        print(msg)


# Setup logger object
logger = logging.getLogger(__name__)
journald_handler = JournalHandler()
journald_handler.setFormatter(
    logging.Formatter('[%(levelname)s] %(message)s'))
logger.addHandler(journald_handler)
logger.setLevel(logging.DEBUG)

debug_handler = debug_logger()
logger.addHandler(debug_handler)

# Setup bot variables
load_dotenv()
APP_DIR = os.getenv('APP_DIR')
TOKEN = os.getenv('DISCORD_TOKEN')

# Setup intents
# https://discordpy.readthedocs.io/en/latest/api.html?highlight=intents#discord.Intents.default
intents = discord.Intents.default()
intents.members = True

BOT = commands.Bot(command_prefix=os.getenv('PREFIX'),
                   intents=intents, case_insensitive=True)

Common = Common()
Common.set_guild(BOT)


@BOT.event
async def on_ready():
    """Produces log for when the bot is ready for action"""
    logger.info(f'{BOT.user.name} has connected to Discord!')


@BOT.command(name="members", aliases=["member"])
async def members(ctx):
    """
    Prints the number of members in the member role.
    """
    role_name = "Member"

    role = utils.get(ctx.guild.roles, name=role_name)
    member = ctx.author

    if role in member.roles:
        message = f'{member.mention} has agreed to the rules.'
    else:
        message = f'{member.mention} has not yet agreed to the rules.'

    member_count = len(role.members)

    embed_data = {
        "title": f'Member Role Total',
        "description": f'{member_count} people have agreed to the rules.\n\n{message}'
    }

    embed = discord.Embed.from_dict(embed_data)
    await ctx.channel.send(embed=embed)


@BOT.event
async def on_command_error(ctx, error):
    """
    Core error handler
    https://discordpy.readthedocs.io/en/latest/ext/commands/api.html?highlight=commands%20check#discord.ext.commands.check
    https://discordpy.readthedocs.io/en/latest/ext/commands/api.html?highlight=commands%20errors#exceptions
    """
    if isinstance(error, commands.errors.MissingPermissions):
        logger.info(
            f'{ctx.author} attempted to run command: {ctx.message.content}')
        if Common.ctx_is_lobby(ctx):
            await ctx.send(f'{ctx.author.mention} You do not have access to run this command.')
        else:
            # Delete unauthorized commands that come from outside a lobby
            await ctx.message.delete()
    elif isinstance(error, Common.UserError):
        await ctx.send(f'{ctx.author.mention} {error.message}')
    elif isinstance(error, commands.errors.UserNotFound) or isinstance(error, commands.errors.MemberNotFound):
        await ctx.send(f'{ctx.author.mention} {error}')
    else:
        logger.error(
            f'Unknown error. Invocation: {ctx.message.content}. \nError: {error}')

# Import custom cogs
self_roles.setup(BOT, logger)
server_stats.setup(BOT, logger)
admin_logging.setup(BOT, logger)
server_rules.setup(BOT, logger)
admin_commands.setup(BOT, logger)
lobby_commands.setup(BOT, logger, APP_DIR)
lobby_handler.setup(BOT, logger)
start_here.setup(BOT, logger)

BOT.run(TOKEN)

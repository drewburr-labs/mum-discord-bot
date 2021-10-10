# bot-main.py
""" centralstation-bot"""

import os
import logging
# from systemd.journal import JournalHandler

from disnake.ext import commands
import disnake

from src.common import Common
import src.self_roles as self_roles
import src.admin_logging as admin_logging
import src.server_rules as server_rules
import src.admin_commands as admin_commands
import src.lobby_commands as lobby_commands
import src.lobby_handler as lobby_handler
import src.start_here as start_here
import src.global_commands as global_commands

Common = Common()


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
debug_handler = debug_logger()
logger.addHandler(debug_handler)

# Setup bot variables
PREFIX = '!'
APP_DIR = os.getenv('PWD')  # Given by Docker
TOKEN = os.getenv('DISCORD_TOKEN')

# Setup intents
# https://disnake.readthedocs.io/en/latest/api.html?highlight=intents#discord.Intents.default
intents = disnake.Intents.default()
intents.members = True

BOT = commands.Bot(command_prefix=PREFIX,
                   intents=intents, case_insensitive=True)


@BOT.event
async def on_ready():
    """Produces log for when the bot is ready for action"""
    logger.info(f'{BOT.user.name} has connected to Discord!')

    admin_logger = BOT.get_cog('admin_logging')

    for guild in BOT.guilds:
        await admin_logger.bot_log(guild, f"{BOT.user.name} has reconnected!")


@BOT.event
async def on_command_error(ctx, error):
    """
    Core error handler
    https://disnake.readthedocs.io/en/latest/ext/commands/api.html?highlight=commands%20check#discord.ext.commands.check
    https://disnake.readthedocs.io/en/latest/ext/commands/api.html?highlight=commands%20errors#exceptions
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
        print('UserError')
        await ctx.send(f'{ctx.author.mention} {error.message}')
    elif isinstance(error, Common.AdminError):
        print('AdminError')
        admin_logger = BOT.get_cog('admin_logging')
        await admin_logger.bot_log(ctx.guild, f'{ctx.author.mention} {error.message}')
    elif isinstance(error, Common.SilentError):
        print('SilentError')
        logger.error(f'Error: {error}\n  - Invocation: {ctx.message.content}.')
    elif isinstance(error, commands.errors.UserNotFound) or isinstance(error, commands.errors.MemberNotFound):
        await ctx.send(f'{ctx.author.mention} {error}')
    else:
        logger.error(
            f'Unknown error. Invocation: {ctx.message.content}. \nError: {error}')

# Import custom cogs
self_roles.setup(BOT, logger)
admin_logging.setup(BOT, logger)
server_rules.setup(BOT, logger)
admin_commands.setup(BOT, logger)
lobby_commands.setup(BOT, logger, APP_DIR)
lobby_handler.setup(BOT, logger)
start_here.setup(BOT, logger)
global_commands.setup(BOT, logger)

BOT.run(TOKEN)

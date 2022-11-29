# bot-main.py
"""centralstation-bot"""

import os
import logging
# from systemd.journal import JournalHandler

from discord.ext import commands
import discord
import asyncio

from src.common import Common
import src.admin_logging as admin_logging
import src.lobby_commands as lobby_commands
import src.lobby_handler as lobby_handler

Common = Common()


class debug_logger:
    # Logger meant for debugging at the terminal.

    level = logging.DEBUG

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
logger.setLevel(logging.DEBUG)
logger.addHandler(debug_logger())

# Setup bot variables
PREFIX = '/'
APP_DIR = os.getenv('PWD')  # Given by Docker
TOKEN = os.getenv('DISCORD_TOKEN')

# Setup intents
# https://discord.readthedocs.io/en/latest/api.html?highlight=intents#discord.Intents.default
intents = discord.Intents.default()
intents.message_content = True
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

    # Sync application commands across all guilds
    await BOT.tree.sync()


@BOT.tree.error
async def on_error(interaction: discord.Interaction, error: discord.app_commands.AppCommandError):
    if isinstance(error, discord.app_commands.errors.CommandOnCooldown):
        logger.warning(f'CommandOnCooldown: {error}')
        await interaction.response.send_message(f"Command is on cooldown. Try again in {error.retry_after:.0f} seconds.")
    elif isinstance(error, Common.UserError):
        logger.warning(f'UserError: {error}')
        await interaction.response.send_message(error.message)
    else:
        logger.warning(f'Unknown error: {error}')
        await interaction.response.send_message("There was an error while handling your command.")


async def start_bot():
    """
    Import custom cogs and start bot
    """
    await admin_logging.setup(BOT, logger)
    await lobby_commands.setup(BOT, logger, APP_DIR)
    await lobby_handler.setup(BOT, logger)
    await BOT.start(TOKEN)

asyncio.run(start_bot())

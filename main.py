# bot-main.py
"""centralstation-bot"""

import os
import logging

from discord.ext import commands
import discord
import asyncio

from src.common import Common
import src.admin_logging as admin_logging
import src.lobby_commands as lobby_commands
import src.lobby_handler as lobby_handler
import src.admin_events as admin_events

Common = Common()

match os.getenv("LOG_LEVEL") or "info":
    case "debug":
        level = logging.DEBUG
    case "info":
        level = logging.INFO
    case "warning":
        level = logging.WARNING
    case "error":
        level = logging.ERROR
    case "critical":
        level = logging.CRITICAL

logging.basicConfig(
    format="%(asctime)s %(levelname)-8s %(message)s",
    level=level,
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)

# Setup bot variables
PREFIX = "/"
APP_DIR = os.getenv("PWD")  # Given by Docker
TOKEN = os.getenv("DISCORD_TOKEN")
CONTROLLER_GUILD_ID = int(os.getenv("CONTROLLER_GUILD_ID") or 1154917737827684372)
CONTROLLER_CHANNEL_ID = int(os.getenv("CONTROLLER_CHANNEL_ID") or 1155579990373568522)

# Setup intents
# https://discord.readthedocs.io/en/latest/api.html?highlight=intents#discord.Intents.default
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

BOT = commands.Bot(command_prefix=PREFIX, intents=intents, case_insensitive=True)


@BOT.event
async def on_ready():
    """Produces log for when the bot is ready for action"""
    logger.info(f"{BOT.user.name} has connected to Discord!")

    admin_logger = BOT.get_cog("admin_logging")

    await admin_logger.log(f"{BOT.user.name} has reconnected!")

    # Sync application commands across all guilds
    await BOT.tree.sync()


@BOT.tree.error
async def on_error(
    interaction: discord.Interaction = None,
    error: discord.app_commands.AppCommandError = None,
):
    try:
        if isinstance(error, discord.app_commands.errors.CommandOnCooldown):
            logger.warning(f"CommandOnCooldown: {error}")
            await interaction.response.send_message(
                f"Command is on cooldown. Try again in {error.retry_after:.0f} seconds."
            )
        elif isinstance(error, Common.UserError):
            logger.warning(f"UserError: {error}")
            await interaction.response.send_message(error.message)
        else:
            logger.warning(f"Unknown error: {error}")
            await interaction.response.send_message(
                "There was an error while handling your command."
            )
    except Exception as e:
        logger.warn("Failed to log on_error exception")
        logger.warn(f"Exception: {e}")
        admin_logger = BOT.get_cog("admin_logging")
        await admin_logger.log(
            f"Failed to log during AppCommandError exception\n\nSource Interaction: \n{interaction}\n\nSource Error: {error}\n\nLogger exception: {e}"
        )


async def start_bot():
    """
    Import custom cogs and start bot
    """
    await admin_logging.setup(BOT, logger, CONTROLLER_GUILD_ID, CONTROLLER_CHANNEL_ID)
    await admin_events.setup(BOT, logger)
    await lobby_commands.setup(BOT, logger, APP_DIR)
    await lobby_handler.setup(BOT, logger)
    await BOT.start(TOKEN)


asyncio.run(start_bot())

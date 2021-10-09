# global.py
# Commands that can be used globally on the server

"""
Commands that can be used anyone, anywhere.
"""

from disnake.ext import commands
from disnake import utils


class global_commands(commands.Cog):
    def __init__(self, bot, logger):
        self.bot = bot
        self.logger = logger


def setup(bot, logger):
    bot.add_cog(global_commands(bot, logger))

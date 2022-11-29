# admin_logging.py
"""
admin_logging is used to log messages that admins are interested in.
"""

from discord.ext import commands
from discord import utils


class admin_logging(commands.Cog):
    def __init__(self, bot, logger):
        self.bot: commands.Bot = bot
        self.logger = logger
        self.bot_log_channel_name = 'bot-logs'

    async def bot_log(self, guild, msg=None, embed=None):
        """
        Sends a message to the defined bot_log_channel_name.
        """
        channel = utils.get(guild.text_channels,
                            name=self.bot_log_channel_name)

        if msg:
            await channel.send(msg)
        else:
            await channel.send(embed=embed)


async def setup(bot: commands.Bot, logger):
    await bot.add_cog(admin_logging(bot, logger))

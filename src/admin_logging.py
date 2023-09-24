# admin_logging.py
"""
admin_logging is used to log messages that admins are interested in.
"""

from discord.ext import commands
from discord import utils
from logging import Logger

class admin_logging(commands.Cog):
    def __init__(self, bot: commands.Bot, logger: Logger, guild_id: int, channel_id: int):
        self.bot: commands.Bot = bot
        self.logger = logger
        self.guild_id= guild_id
        self.channel_id = channel_id

    def _get_guild(self):
        return utils.get(self.bot.guilds, id=self.guild_id)

    async def log(self, msg=None, embed=None):
        """
        Sends a message to the defined bot_log_channel_name.
        """
        guild = self._get_guild()

        channel = utils.get(guild.text_channels,
                            id=self.channel_id)

        try:
            if msg:
                await channel.send(msg)

            if embed:
                await channel.send(embed=embed)
        except Exception as e:
            self.logger.error("Failed to admin log message")
            self.logger.error(e)


        if not (msg or embed):
            await channel.send("`bot_log()` was called without any arguments!")




async def setup(bot: commands.Bot, logger: Logger, guild_id: int, channel_id: int):
    await bot.add_cog(admin_logging(bot, logger, guild_id, channel_id))

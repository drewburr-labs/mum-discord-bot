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
        self.leave_channel_name = 'leave-log'
        self.bot_log_channel_name = 'bot-logs'

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        channel = utils.get(
            member.guild.text_channels, name=self.leave_channel_name)
        await channel.send(f"{member.display_name} ({member.name}#{member.discriminator}) has left the server.")

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

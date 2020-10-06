# server_stats.py
"""
server_stats is used to update server statistics.

There is a limit of 2 updates per 10 min for channel names/topics. For this reason, stats are updated every 10 minutes.

Statistic channels are expected to be voice channels. Ideally, these would deny @everyone the connect permission
"""

from dotenv import load_dotenv
from discord.ext import tasks, commands
from discord import utils
import discord


class server_stats(commands.Cog):
    def __init__(self, bot, logger):
        self.bot = bot
        self.logger = logger
        self.category = None  # The expected category for each stat channel
        self.update_stats.start()  # Start the task loop

    @tasks.loop(minutes=10)
    async def update_stats(self):
        """
        Executes all statistic update functions. Can only be a member of one guild.
        """
        if len(self.bot.guilds) > 1:
            self.logger.warning(
                'Bot is a member of multiple guilds! Unable to update stats.')
        else:
            guild = self.bot.guilds[0]

        await self.update_member_count(guild)
        self.logger.info('Server statistics have been updated.')

    @update_stats.before_loop
    async def wait_for_ready(self):
        """
        Wait until the bot is ready.
        """
        await self.bot.wait_until_ready()

    async def update_member_count(self, guild):
        """
        Responsible for managing the member count statistic
        """
        channel_prefix = 'Member Count:'

        for channel in guild.voice_channels:
            if channel.category is self.category and channel.name.startswith(channel_prefix):
                member_count = len(channel.guild.members)
                await channel.edit(name=f'{channel_prefix} {member_count}')


def setup(bot, logger):
    bot.add_cog(server_stats(bot, logger))
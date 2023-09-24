# admin_logging.py
"""
admin_logging is used to log messages that admins are interested in.
"""

from discord.ext import commands
import discord
from logging import Logger
from .common import Common


class admin_events(commands.Cog):
    def __init__(self, bot: commands.Bot, logger: Logger):
        self.bot: commands.Bot = bot
        self.logger = logger
        self.admin_logger = bot.get_cog("admin_logging")

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        await self.log_guild_membership_change(guild, "New server joined!")

        welcome_embed = self.get_welcome_message()

        # Send welcome message to first text channel
        await guild.text_channels[0].send(embeds=[welcome_embed])

        # Send welcome message to server owner
        if guild.owner:
            if not guild.owner.dm_channel:
                await guild.owner.create_dm()
            await guild.owner.dm_channel.send(embeds=[welcome_embed])

    @commands.Cog.listener()
    async def on_guild_remove(self, guild: discord.Guild):
        await self.log_guild_membership_change(guild, "Left server!")


    async def log_guild_membership_change(self, guild, title):
        embed_data = {
            "title": title,
            "description": f"{self.bot.application.name} is now a member of {len(self.bot.guilds)} servers",
            "fields": [
                {
                    "name": "Name",
                    "value": guild.name,
                },
                {
                    "name": "Description",
                    "value": guild.description or "No server discription",
                },
                {
                    "name": "Owner",
                    "value": f"Name: {guild.owner.name}, ID: {guild.owner.id}",
                },
                {
                    "name": "Members",
                    "value": guild.member_count,
                },
            ],
        }
        embed = discord.Embed.from_dict(embed_data)
        await self.admin_logger.log(embed=embed)

    def get_welcome_message(self):
        embed_data = {
            "title": "Thanks for inviting me to your server!",
            "description": "Here's some info to help get started",
            "fields": [
                {
                    "name": "Documentation",
                    "value": f"Setup steps, behavior, and usage are all documented in GitHub:\n{Common.github_url}",
                },
                {
                    "name": "Discord server",
                    "value": f"Join the official Discord server to learn more about Mum, hear about upcoming maintenance, request new features, and report any bugs. Come say hello and ask any qustions!\n{Common.discord_invite}",
                },
            ],
        }
        embed = discord.Embed.from_dict(embed_data)
        return embed

async def setup(bot: commands.Bot, logger: Logger):
    await bot.add_cog(admin_events(bot, logger))

# start_here.py
"""
start_here
"""

import discord
from discord import utils
from discord.ext import tasks, commands


class start_here(commands.Cog):
    def __init__(self, bot, logger):
        self.bot = bot
        self.logger = logger
        self.channel_name = 'start-here'

    @commands.has_role('Mod')
    @commands.command(name="refresh-start-here")
    async def refresh_channel(self, ctx):
        """
        Sets up the channel to ensure the messages are up to date.
        """
        guild = ctx.guild
        channel = utils.get(
            ctx.guild.text_channels, name=self.channel_name)

        if ctx.channel is channel:
            # Get channel info
            self_roles = utils.get(guild.text_channels, name="self-roles")
            rules = utils.get(guild.text_channels, name="rules")
            introductions = utils.get(
                guild.text_channels, name="introductions")
            bot_user = self.bot.user

            # Delete all messages in the channel
            await channel.purge()

            # Publish message
            embed_data = {
                "title": f"Welcome to {ctx.guild.name}!",
                "description": f"We started as a community who played Among Us, and have grown into a group of friends who span many games and interests. If you're new here, take a second to say hello in {introductions.mention}.",
                "fields":
                [
                    {
                        "name": "Creating voice channels",
                        "value": f"Create new voice channels by joining the **Create New Lobby** voice channel. Each lobby comes with a private text-chat, that only the voice channel can see."
                    },
                    {
                        "name": "Say hi to Mum!",
                        "value": f"This server is powered by our custom bot - {bot_user.mention}. If you ever need help, try using the `!help` command.\nNote: Some commands are context-sensitive. Try using `!help` in a lobby text-chat!"
                    },
                    {
                        "name": "Join our Steam group",
                        "value": "Find and play with members of the community by joining our Steam group\nhttps://steamcommunity.com/groups/CentralStation"
                    },
                    {
                        "name": "Self Roles",
                        "value": f"Check out the {self_roles.mention} channel to add yourself to pingable community roles, or change your color."
                    },
                    {
                        "name": "Agree to the Rules",
                        "value": f"Read through the rules {rules.mention} to get access to the rest of the server. These are expectations that apply to all members, including mods."
                    },
                ]
            }

            embed = discord.Embed.from_dict(embed_data)
            await channel.send(embed=embed)


def setup(bot, logger):
    bot.add_cog(start_here(bot, logger))

# new_member_logic.py
"""
Handles processing of new members to ensure they agree to the rules and read initial server info.
"""

from dotenv import load_dotenv
from discord.ext import tasks, commands
from discord import utils
import discord
import asyncio


class new_member_logic(commands.Cog):
    def __init__(self, bot, logger):
        self.bot = bot
        self.logger = logger
        self.channel_name = "start-here"
        self.member_role = "Member"
        self.accept_msg = "I have read and accept the rules"

    @commands.Cog.listener(name="on_message")
    async def initialize_member(self, message):
        """
        Adds a user to the member_role

        Role will only be assigned if message is {self.accept_msg}
        Deletes all messages in {self.channel}
        """
        guild = message.guild
        member_role = utils.get(guild.roles, name=self.member_role)
        channel = utils.get(guild.text_channels, name=self.channel_name)

        if message.channel is channel:
            if message.content.lower() == self.accept_msg.lower():
                await message.author.add_roles(member_role)
                self.logger.info(
                    f"{message.author.name} has agreed to the rules.")
                await message.author.send("Thank you for agreeing to the rules. We hope you enjoy the community!")

            if not message.embeds:
                await asyncio.sleep(1)
                await message.delete()

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
            server_info = utils.get(guild.text_channels, name="server-info")
            self_roles = utils.get(guild.text_channels, name="self-roles")
            rules = utils.get(guild.text_channels, name="rules")

            # Delete all messages in the channel
            await channel.purge()

            # Publish message
            embed_data = {
                "title": f"Welcome to {ctx.guild.name}!",
                "description": "Here's a bit of info to help get you started.",
                "fields":
                [
                    {
                        "name": "General Server Information",
                        "value": f"For information about the server and channels, please see the {server_info.mention} channel."
                    },
                    {
                        "name": "Server Rules",
                        "value": f"Please make sure to take time to read through the {rules.mention}. These are expectations that apply to all members, including mods."
                    },
                    {
                        "name": "Self Roles",
                        "value": f"Check out the {self_roles.mention} channel to change your color, assign yourself to a region, and subscribe to new game notifications."
                    },
                    {
                        "name": "Agree to the Rules",
                        "value": f"Once you've read through the {rules.mention}, send 'I have read and accept the rules' to this channel. This will grant you access to the rest of the server."
                    },
                ]
            }

            embed = discord.Embed.from_dict(embed_data)
            await channel.send(embed=embed)


def setup(bot, logger):
    bot.add_cog(new_member_logic(bot, logger))

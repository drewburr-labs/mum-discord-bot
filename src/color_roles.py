# color_roles.py
"""
color_roles is used to allow members to change their username color to match their crewmate color.

This should be handled by a single message being in the 'color-roles' text channel, which will update roles based on reactions.
"""

from dotenv import load_dotenv
from discord.ext import commands
from discord import utils
import discord


class color_roles(commands.Cog):
    def __init__(self, bot, logger):
        self.bot = bot
        self.logger = logger
        self.channel_name = 'color-roles'
        self.reaction_message = None

        self.color_map = (
            ('crewmate_red', 'Red'),
            ('crewmate_orange', 'Orange'),
            ('crewmate_yellow', 'Yellow'),
            ('crewmate_lime', "Lime"),
            ('crewmate_darkgreen', 'Dark Green'),
            ('crewmate_cyan', 'Cyan'),
            ('crewmate_blue', 'Blue'),
            ('crewmate_purple', "Purple"),
            ('crewmate_pink', 'Pink'),
            ('crewmate_brown', 'Brown'),
            ('crewmate_black', 'Black'),
            ('crewmate_white', 'White'),
            ('no', 'Remove Color')
        )

    @commands.command(name="refresh")
    async def refresh_role_channel(self, ctx):
        """
        Sets up the color_roles channel to ensure the messages are up to date.
        """

        role_channel = utils.get(
            ctx.guild.text_channels, name=self.channel_name)

        if ctx.channel is role_channel:
            # Delete all messages in the channel
            await role_channel.purge()

            # Publish new messages
            await self.setup_channel(role_channel)

    async def setup_channel(self, channel):
        """
        Adds message and reactions to the color_roles channel.
        """

        # Get emojis for later use
        emoji_data = dict()
        for item in self.color_map:
            role = item[0]
            color_text = item[1]
            emoji = utils.get(channel.guild.emojis, name=role)

            emoji_data[color_text] = emoji

        # Setup embed message
        message_text = ""
        for color_text, emoji in emoji_data.items():
            emoji_text = f"<:{emoji.name}:{emoji.id}>"
            message_text += f"{emoji_text} **| {color_text}**\n"

        # https://discordpy.readthedocs.io/en/latest/api.html#embed
        embed_data = {
            "title": "Color Roles",
            "description": "Below is a list of colors that map to Crewmate colors! React to this message to get the assigned color.",
            "fields":
            [
                {
                    "name": "Color Selection",
                    "value": message_text,
                }
            ]
        }

        embed = discord.Embed.from_dict(embed_data)

        message = await channel.send(embed=embed)

        # Adds emojis to message, as listed in color_roles.
        for emoji in emoji_data.values():
            await message.add_reaction(emoji)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):

        print('Reaction added!')
        print(payload)

        # guild = payload.guild
        channel_id = payload.channel_id
        message_id = payload.message_id
        member = payload.member
        emoji = payload.emoji

        if not member.bot:
            role_channel = utils.get(
                member.guild.text_channels, name=self.channel_name)

            if channel_id == role_channel.id:

                # Remove the member's reaction
                message = await role_channel.fetch_message(message_id)
                await message.remove_reaction(emoji, member)

                for item in self.color_map:
                    if item[0] == emoji.name:
                        role_name = item[1]

                # Assign role
                role = utils.get(member.guild.roles, name=role_name)
                await member.add_roles(role)


def setup(bot, logger):
    bot.add_cog(color_roles(bot, logger))

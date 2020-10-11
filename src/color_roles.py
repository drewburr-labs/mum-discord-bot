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

        self.color_roles_title = 'Color Roles'
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

        self.crewmate_role_title = 'Crewmates Roles'
        self.crewmate_role_map = (
            ('bigbrain', 'Crewmates'),
            ('no', 'Remove Role')
        )

    @commands.command(name="refresh")
    async def refresh_role_channel(self, ctx):
        """
        Sets up the roles channel to ensure the messages are up to date.
        """

        role_channel = utils.get(
            ctx.guild.text_channels, name=self.channel_name)

        if ctx.channel is role_channel:
            # Delete all messages in the channel
            await role_channel.purge()

            # Publish new messages
            await self.send_color_roles_msg(role_channel)
            # await self.send_crewmate_role_msg(role_channel)

    async def send_color_roles_msg(self, channel):
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
            "title": self.color_roles_title,
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
        """
        Handles determining if an add reaction is actionable, and what action should be taken

        All reactions must be from a non-bot user, and must be made to a message in the roles channel.

        All messages in the roles channel are assumed to contain a single embed.
        """
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

                if message.embeds[0].title == self.color_roles_title:
                    await self.color_roles_handler(member, emoji)

    async def color_roles_handler(self, member, emoji):
        # Clear any assigned color roles, and cache new role
        new_role = None
        member_roles = member.roles

        for item in self.color_map:
            role_name = item[1]
            emoji_name = item[0]

            role = utils.get(member.guild.roles, name=role_name)
            if role in member_roles:
                await member.remove_roles(role)
                self.logger.info(
                    f'Removed {member.name} from color role {role_name}')

            if emoji_name == emoji.name:
                new_role = role

        # Assign role
        if new_role is not None and new_role.name != 'Remove Color':
            await member.add_roles(new_role)
            self.logger.info(
                f'Added {member.name} to color role {new_role.name}')


def setup(bot, logger):
    bot.add_cog(color_roles(bot, logger))

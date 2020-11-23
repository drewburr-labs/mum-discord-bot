# self_roles.py
"""
self_roles is used to allow members to add or remove themselves from roles.

This should be handled by a single message being in the 'self_roles' text channel, which will update roles based on reactions.
"""

from dotenv import load_dotenv
from discord.ext import commands
from discord import utils
import discord


class self_roles(commands.Cog):
    def __init__(self, bot, logger):
        self.bot = bot
        self.logger = logger
        self.channel_name = 'self-roles'

        # title.reaction_map (set)
        # title.description (str)
        self.message_data = {
            'Color Roles': {
                'reaction_map': (
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
                ),
                'description': 'Below is a list of colors that map to Crewmate colors! React to this message to be given the assigned color.'
            },
            'Region Roles': {
                'reaction_map': (
                    ('crewmate_purple', 'North America'),
                    ('crewmate_pink', 'Europe'),
                    ('crewmate_cyan', 'Asia')
                ),
                'description': 'Select a role to help lobbies determine which region to create games in.'
            },
            'Crewmates Role': {
                'reaction_map': (
                    ('crewmate_yellow', 'Crewmates'),
                    ('no', 'Remove role')
                ),
                'description': 'React to this message to be assigned the Crewmate role. This role can be pinged by members who are looking to create a game.'
            }
        }

    @commands.command(name="colors")
    async def colors(self, ctx):
        """
        Prints the number of members in each color role.
        """
        data = dict()
        color_map = self.message_data['Color Roles']['reaction_map']

        for item in color_map:
            emoji_name = item[0]
            role_name = item[1]

            if emoji_name != 'no':
                emoji = utils.get(ctx.guild.emojis, name=emoji_name)
                role = utils.get(ctx.guild.roles, name=role_name)

                emoji_text = f"<:{emoji.name}:{emoji.id}>"
                member_count = len(role.members)

                data[emoji_text] = member_count

        message = list()
        sorted_data = sorted(data, key=data.get, reverse=True)

        for item in sorted_data:
            message.append(f'{item} - {data[item]}')

        embed_data = {
            "title": f'Color Role Totals',
            "description": '\n'.join(message),
        }

        embed = discord.Embed.from_dict(embed_data)
        await ctx.channel.send(embed=embed)

    @commands.has_role('Mod')
    @commands.command(name="refresh-self-roles")
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
            for title in self.message_data:
                data = self.message_data[title]

                description = data.get('description')
                reaction_map = data['reaction_map']
                await self.send_roles_message(role_channel, title, description, reaction_map)

    async def send_roles_message(self, channel, title, description, reaction_map):
        # Get emojis for later use
        emoji_data = dict()
        for item in reaction_map:
            emoji_name = item[0]
            role_name = item[1]
            emoji = utils.get(channel.guild.emojis, name=emoji_name)

            emoji_data[role_name] = emoji

        # Setup embed message
        message_text = ""
        for color_text, emoji in emoji_data.items():
            emoji_text = f"<:{emoji.name}:{emoji.id}>"
            message_text += f"{emoji_text} **| {color_text}**\n"

        # https://discordpy.readthedocs.io/en/latest/api.html#embed
        embed_data = {
            "title": f'{title}',
            "description": f"{description}\n\n{message_text}",
        }

        embed = discord.Embed.from_dict(embed_data)
        message = await channel.send(embed=embed)

        # Adds emojis to message.
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

                title = message.embeds[0].title
                data = self.message_data.get(title)

                if data is None:
                    self.logger.warn(
                        f'Invalid title in {self.channel_name}: {title}')
                else:
                    # handler = data['handler']
                    await self.roles_handler(member, emoji, data['reaction_map'])

    async def roles_handler(self, member, emoji, reaction_map):
        # Clear any assigned roles, and cache new role
        new_role = None
        member_roles = member.roles

        for item in reaction_map:
            role_name = item[1]
            emoji_name = item[0]

            role = utils.get(member.guild.roles, name=role_name)
            if role in member_roles:
                await member.remove_roles(role)
                self.logger.info(
                    f'Removed {member.name} from role: {role_name}')

            if emoji_name == emoji.name:
                new_role = role

        # Assign role
        if new_role is not None and emoji.name != 'no':
            await member.add_roles(new_role)
            self.logger.info(
                f'Added {member.name} to role: {new_role.name}')


def setup(bot, logger):
    bot.add_cog(self_roles(bot, logger))

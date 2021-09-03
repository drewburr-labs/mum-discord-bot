# self_roles.py
"""
self_roles is used to allow members to add or remove themselves from roles.

This should be handled by a single message being in the 'self_roles' text channel, which will update roles based on reactions.
"""

from discord.ext import commands
from discord import utils
import discord


class self_roles(commands.Cog):
    def __init__(self, bot, logger):
        self.bot = bot
        self.logger = logger
        self.channel_name = 'self-roles'

        # title.reaction_map - set(emoji, role/description)
        # title.description - str
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
                    ('crewmate_white', 'White')
                ),
                'description': 'React to this message to be given the assigned color.'
            },
            'Game Roles': {
                'reaction_map': (
                    ('crewmate_yellow', 'Among Us'),
                    ('creeper_face', 'Minecraft'),
                    ('phasmo_p', 'Phasmophobia'),
                    ('rocket_league', 'Rocket League'),
                    ('ghost', 'Call of Duty'),
                    ('destiny', 'Destiny')
                ),
                'description': "React to this message to be assigned a game-specific role. These role can be pinged by members who are looking to create or organize games."
            }
        }

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

                # Get data from the message reacted to
                message = await role_channel.fetch_message(message_id)
                title = message.embeds[0].title
                data = self.message_data.get(title)

                if data is None:
                    self.logger.warn(
                        f'Invalid title in {self.channel_name}: {title}')
                else:
                    # Get the new role from reaction_map
                    new_role = None

                    for item in data['reaction_map']:
                        role_name = item[1]
                        emoji_name = item[0]

                        role = utils.get(member.guild.roles, name=role_name)

                        if emoji_name == emoji.name:
                            new_role = role

                    # Assign role
                    if new_role is not None:
                        await member.add_roles(new_role)
                        self.logger.info(
                            f'Added {member.name} to role: {new_role.name}')
                    else:
                        existing_reaction = [
                            reaction for reaction in message.reactions if str(reaction.emoji) == str(emoji)]

                        if existing_reaction:
                            await existing_reaction[0].clear()

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        """
        Handles determining if an removed reaction is actionable, and what action should be taken

        All reactions must be from a non-bot user, and must be made to a message in the roles channel.

        All messages in the roles channel are assumed to contain a single embed.
        """
        guild = self.bot.guilds[0]
        channel_id = payload.channel_id
        message_id = payload.message_id
        # payload.member # user_id
        member = utils.get(guild.members, id=payload.user_id)
        emoji = payload.emoji

        if member and not member.bot:
            role_channel = utils.get(
                member.guild.text_channels, name=self.channel_name)

            if channel_id == role_channel.id:

                # Get data from the message reacted to
                message = await role_channel.fetch_message(message_id)
                title = message.embeds[0].title
                data = self.message_data.get(title)

                if data is None:
                    self.logger.warn(
                        f'Invalid title in {self.channel_name}: {title}')
                else:
                    # handler = data['handler']
                    await self.remove_roles_handler(member, emoji, data['reaction_map'])

    async def remove_roles_handler(self, member, emoji, reaction_map):
        # Get the role from reaction_map
        remove_role = None

        for item in reaction_map:
            role_name = item[1]
            emoji_name = item[0]

            role = utils.get(member.guild.roles, name=role_name)

            if emoji_name == emoji.name:
                remove_role = role

        # Remove role
        if remove_role is not None:
            await member.remove_roles(remove_role)
            self.logger.info(
                f'Removed {member.name} from role: {remove_role.name}')

    @commands.has_role('Mod')
    @commands.command(name="refresh-self-roles")
    async def refresh_role_channel(self, ctx):
        """
        Sets up the roles channel to ensure the messages are up to date.
        """
        await ctx.message.delete()

        role_channel = utils.get(
            ctx.guild.text_channels, name=self.channel_name)

        if ctx.channel is role_channel:
            # Get messages
            messages = await role_channel.history(limit=100).flatten()

            # dict{title, message}
            message_dict = dict()

            for msg in messages:
                if msg.embeds:
                    message_dict[msg.embeds[0].title] = msg

            # Publish/update messages
            for title in self.message_data:
                existing_message = message_dict.get(title)

                data = self.message_data[title]
                description = data.get('description')
                reaction_map = data['reaction_map']

                # Get emojis for later use
                emoji_data = dict()
                for item in reaction_map:
                    emoji_name = item[0]
                    role_name = item[1]
                    emoji = utils.get(ctx.guild.emojis, name=emoji_name)

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

                if existing_message is None:
                    # Send message to channel
                    new_message = await role_channel.send(embed=embed)
                else:
                    # Update message with new embed
                    await existing_message.edit(embed=embed)
                    new_message = existing_message

                # Adds emojis to message.
                for emoji in emoji_data.values():
                    await new_message.add_reaction(emoji)


def setup(bot, logger):
    bot.add_cog(self_roles(bot, logger))

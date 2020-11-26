# bot-main.py
""" discord-among-us

This bot is meant to handle a private Among Us game, with several dozen running concurrently.

I like the idea of making this stateless, so no database needed here. Everything should be stored in Discord.

I'm thinking about setting this up so there's a text channel created for every voice channel, and is private for that voice channel (i.e. no one else can see it)

The main purpose here is to allow for a party to join a group, join their private match via the game code (shared through a text channel) and play with voice chat.

Things like setting player limits and creating an auto-join system with categories will come later. Maybe you want 5-6 friends to play together, or only want to join non-nsfw channels.

Thoughts on the auto join system:
Creating private lobbies
Roles - language-specific filters (only German / only english)


"""

import os
import logging
from systemd.journal import JournalHandler

from dotenv import load_dotenv
from discord.ext import commands
from discord import utils
import discord

from src.common import Common
import src.self_roles as self_roles
import src.server_stats as server_stats
import src.admin_logging as admin_logging
import src.server_rules as server_rules
import src.admin_commands as admin_commands
import src.lobby_commands as lobby_commands

Common = Common()


class debug_logger:
    # Logger meant for debugging at the terminal.

    level = 0

    def handle(self, record):
        self.emit(record)

    def handleError(self, record):
        self.emit(record)

    def emit(self, record):
        # https://docs.python.org/3/library/logging.html#logrecord-objects
        # Extracts the log message for terminal printing
        # Formatting: filename, line_number, message
        msg = f"{record.pathname}, {record.lineno}, \"{record.msg}\""
        print(msg)


# Setup logger object
logger = logging.getLogger(__name__)
journald_handler = JournalHandler()
journald_handler.setFormatter(
    logging.Formatter('[%(levelname)s] %(message)s'))
logger.addHandler(journald_handler)
logger.setLevel(logging.DEBUG)

debug_handler = debug_logger()
logger.addHandler(debug_handler)

# Setup bot variables
load_dotenv()
APP_DIR = os.getenv('APP_DIR')
TOKEN = os.getenv('DISCORD_TOKEN')

# Setup intents
# https://discordpy.readthedocs.io/en/latest/api.html?highlight=intents#discord.Intents.default
intents = discord.Intents.default()
intents.members = True

BOT = commands.Bot(command_prefix=os.getenv('PREFIX'),
                   intents=intents, case_insensitive=True)


@BOT.event
async def on_ready():
    """Produces log for when the bot is ready for action"""
    logger.info(f'{BOT.user.name} has connected to Discord!')


@BOT.event
async def on_voice_state_update(member, before, after):
    """
    Handler for automatically managing lobbies.
    Should not be modifying anything under the General category.

    Create a new lobby when user joins seed_channel.
    New channel will use the same configuration from seed_channel.

    Delete any empty lobbies.
    """

    # Don't do anything if user's channel didn't update
    if before.channel is not after.channel:

        guild = member.guild
        seed_channel = utils.get(guild.voice_channels, name='Create New Lobby')

        # If user joined a channel
        if after.channel is not None:
            if after.channel is seed_channel:
                # User has joined the seed channel. Create a new lobby.
                await initialize_lobby(guild, seed_channel, member)

            elif Common.is_lobby(after.channel.category):
                # User is joining an existing lobby
                await initialize_lobby_member(member, after.channel.category)

        # If user left a lobby
        if before.channel is not None and Common.is_lobby(before.channel.category):
            # Clear member's roles from last lobby
            await clear_member_lobby_overwrites(member, before.channel.category)

            # If the last lobby is empty, delete it
            if not before.channel.members:
                await delete_lobby(before.channel.category)


async def initialize_lobby_member(member, category):
    """
    Grants a user access to the currently joined lobby.
    Assumes the current lobby exists, and the member is still present in the lobby.
    """

    # Grant read access to text channels
    for text_channel in category.text_channels:
        await text_channel.set_permissions(member, read_messages=True)


async def initialize_lobby_text_channel(category):
    """
    Creates the text channel for a particular lobby.

    Text channel is hidden from users with the default role.

    Retuns the created text channel.
    """
    guild = category.guild
    text_channel_name = "text-chat"

    # Setup overwrites
    default_overwrite = discord.PermissionOverwrite(read_messages=False)

    overwrites = {
        # Text channels are invisible by default
        guild.default_role: default_overwrite
    }

    # Setup text channel
    text_channel = await category.create_text_channel(text_channel_name, overwrites=overwrites)

    await send_lobby_welcome_message(text_channel)

    return text_channel


async def initialize_lobby_voice_channel(category, seed_channel):
    """
    Creates the voice channel for a particular lobby.

    Retuns the created voice channel.
    """
    voice_channel_name = "voice chat"

    voice_channel_params = {
        "bitrate": seed_channel.bitrate,
        "user_limit": 10,
    }

    voice_channel = await category.create_voice_channel(voice_channel_name, **voice_channel_params)

    return voice_channel


# @BOT.command(name="test")
async def send_lobby_welcome_message(text_channel):

    # text_channel = utils.get(ctx.guild.text_channels, name='general')
    prefix = BOT.command_prefix

    # https://discordpy.readthedocs.io/en/latest/api.html#embed
    embed_data = {
        "title": "Welcome to the lobby!",
        "description": "Here's some tips to get you started",
        "fields":
        [
            {
                "name": "Managing the lobby",
                "value": f"By default, the creator of the lobby has the ability to manage channels, mute members, etc. To grant these privileges to another lobby member, use the `{prefix}promote @user` command.",
            },
            {
                "name": "Lobby text channels are private",
                "value": "Only those in the lobby's voice chat can see the text channel. You'll want to share game codes here.",
            },
            {
                "name": f"The `{prefix}code` command",
                "value": f"Use the `{prefix}code` command to communicate game codes. Use this command to get the current game code, or set a new one with `{prefix}code ABCXYZ`. This command also has the alias `{prefix}c`.",
            },
            {
                "name": f"Need a map?",
                "value": f"Have a new player, or forget the locations of cameras and vents? The `{prefix}map` command is here to help! **Tip:** Maps can also be requested by name `{prefix}map Polus`."
            },
            {
                "name": "Vote on a map",
                "value": f"Use the `{prefix}mapvote` command to vote on the map to play next."
            },
            {
                "name": "Kicking a user",
                "value": f"If a member needs to be removed from a lobby, you can vote to kick a user with the `{prefix}votekick` command. Usage `{prefix}votekick @drewburr Reason for kicking`",
            },
        ]
    }

    embed = discord.Embed.from_dict(embed_data)

    await text_channel.send(embed=embed)


async def initialize_lobby(guild, seed_channel, member):
    """
    Creates a lobby (category) named after the member.

    Adds a text and voice channel to the category.
    Creates a role to grant access to the text channel.

    The creating member will be granted access to manage the channels in this category.
    """

    # Generate a lobby, based on the username
    # Drewburr's Lobby
    category_name = f"{member.display_name}'s Lobby"

    category = await guild.create_category(category_name)

    # Create the lobby voice channel
    voice_channel = await initialize_lobby_voice_channel(category, seed_channel)

    # Create voice channel and setup permissions
    await initialize_lobby_text_channel(category)

    # Grant user default access to the lobby
    await initialize_lobby_member(member, category)

    # Move the user to the lobby. Triggers 'on_voice_state_update'
    logger.info(
        f'Moving {member.display_name} to channel: {voice_channel.name}')
    await member.edit(voice_channel=voice_channel)


async def delete_lobby(category):
    """
    Handles the deletion of an existing lobby.

    Assumes lobby still exists.
    """

    channels = category.channels
    category_roles = list()

    logger.info(f'Deleting empty category: {category}')

    # Delete all channels
    for channel in channels:
        category_roles.extend(channel.changed_roles)

        print("Deleting channel: " + channel.name)
        await channel.delete()

    # Delete category
    print("Deleting category: " + category.name)
    category_roles.extend(category.changed_roles)
    await category.delete()

    # Delete any non-default roles
    for role in category_roles:
        if not role.is_default():
            print("Deleting role: " + role.name)
            await role.delete()


async def clear_member_lobby_overwrites(member, category):
    """
    Clears a user's permission overwrites from a lobby.

    Permssion overwrites are those that differ from the category.
    """

    channels = category.channels

    overwrite = discord.PermissionOverwrite()

    # Remove all channel permission overwrites
    for channel in channels:
        await channel.set_permissions(member, overwrite=overwrite)

    # Remove the lobby permission overwrites
    await category.set_permissions(member, overwrite=overwrite)


@BOT.command(name="members", aliases=["member"])
async def members(ctx):
    """
    Prints the number of members in the member role.
    """
    role_name = "Member"

    role = utils.get(ctx.guild.roles, name=role_name)
    member = ctx.author

    if role in member.roles:
        message = f'{member.mention} has agreed to the rules.'
    else:
        message = f'{member.mention} has not yet agreed to the rules.'

    member_count = len(role.members)

    embed_data = {
        "title": f'Member Role Total',
        "description": f'{member_count} people have agreed to the rules.\n\n{message}'
    }

    embed = discord.Embed.from_dict(embed_data)
    await ctx.channel.send(embed=embed)


@BOT.event
async def on_command_error(ctx, error):
    """
    Core error handler
    https://discordpy.readthedocs.io/en/latest/ext/commands/api.html?highlight=commands%20check#discord.ext.commands.check
    https://discordpy.readthedocs.io/en/latest/ext/commands/api.html?highlight=commands%20errors#exceptions
    """
    if isinstance(error, commands.errors.MissingPermissions):
        logger.info(
            f'{ctx.author} attempted to run command: {ctx.message.content}')
        if Common.ctx_is_lobby(ctx):
            await ctx.send(f'{ctx.author.mention} You do not have access to run this command.')
        else:
            # Delete unauthorized commands that come from outside a lobby
            await ctx.message.delete()
    elif isinstance(error, Common.UserError):
        await ctx.send(f'{ctx.author.mention} {error.message}')
    elif isinstance(error, commands.errors.UserNotFound) or isinstance(error, commands.errors.MemberNotFound):
        await ctx.send(f'{ctx.author.mention} {error}')
    else:
        logger.error(
            f'Unknown error. Invocation: {ctx.message.content}. \nError: {error}')

# Import custom cogs
self_roles.setup(BOT, logger)
server_stats.setup(BOT, logger)
admin_logging.setup(BOT, logger)
server_rules.setup(BOT, logger)
admin_commands.setup(BOT, logger)
lobby_commands.setup(BOT, logger, APP_DIR)

BOT.run(TOKEN)

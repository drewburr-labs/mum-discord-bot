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
import random
import logging
from datetime import datetime
from systemd.journal import JournalHandler

from dotenv import load_dotenv
from discord.ext import commands
from discord import utils
import discord


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
TOKEN = os.getenv('DISCORD_TOKEN')
BOT = commands.Bot(command_prefix=os.getenv('PREFIX'))


# Define custom exception
class LocationError(discord.ext.commands.CommandError):
    """
    A command was run from a forbidden location.
    Example: User executes a lobby-specific command in #general

    Attributes:
        message -- Error message to send to chat, as a reply.
    """

    def __init__(self, message):
        self.message = message


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

            elif is_lobby(after.channel.category):
                # User is joining an existing lobby
                await initialize_lobby_member(member, after.channel.category)

        # If user left a lobby
        if before.channel is not None and is_lobby(before.channel.category):
            # Clear member's roles from last lobby
            await clear_member_lobby_overwrites(member, before.channel.category)

            # If the last lobby is empty, delete it
            if not before.channel.members:
                await delete_lobby(before.channel.category)


def is_lobby(category):
    """
    Returns True (bool) if a category is a lobby.
    """

    if category.name.endswith("Lobby"):
        return True
    else:
        return False


def ctx_is_lobby(ctx):
    """
    Checks if a message was sent from a lobby's text channel.
    Raises LocationError if channel is not a lobby.
    """
    if is_lobby(ctx.channel.category):
        return True
    else:
        raise LocationError('That command can only be used in a lobby.')


async def initialize_lobby_member(member, category):
    """
    Grants a user access to the currently joined lobby.
    Assumes the current lobby exists, and the member is still present in the lobby.
    """

    # Grant read access to text channels
    for text_channel in category.text_channels:
        await text_channel.set_permissions(member, read_messages=True)


async def initialize_lobby_admin(member, category):
    """
    Grants a user 'admin' control over the current lobby.
    Assumes the current lobby exists, and the member is still present in the lobby.
    """

    channels = category.channels

    discord.PermissionOverwrite(
        manage_channels=True, mute_members=True)

    # Update user's permission overwrites
    for channel in channels:
        overwrite = channel.overwrites_for(member)
        overwrite.update(manage_channels=True, mute_members=True)

        await channel.set_permissions(member, overwrite=overwrite)


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
                "name": "Managing your lobby",
                "value": f"By default, the creator of the lobby has the ability to manage channels, mute members, etc. To grant these privileges to another lobby member, use the `{prefix}promote @user` command.",
            },
            {
                "name": "Lobby text channels are private",
                "value": "Only those in the lobby's voice chat can see the text channel. You'll want to share game codes here.",
            },
            {
                "name": f"The `{prefix}code` command",
                "value": f"Use the `{prefix}code ABCXYZ` command to rename your text channel after your game code. This command also has the alias `{prefix}c`.",
            },
            # {
            #     "name": "Field2",
            #     "value": "This is a message?",
            # },
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

    # Generate a voice channel name, based on the username
    # Drewburr's channel
    category_name = f"{member.name}'s Lobby"

    category = await guild.create_category(category_name)

    # Create the lobby voice channel
    voice_channel = await initialize_lobby_voice_channel(category, seed_channel)

    # Create voice channel and setup permissions
    await initialize_lobby_text_channel(category)

    # Grant user default access to the lobby
    await initialize_lobby_member(member, category)

    # Grant user "admin" access to the lobby
    await initialize_lobby_admin(member, category)

    # Move the user to the lobby. Triggers 'on_voice_state_update'
    logger.info(
        f'Moving {member.name} to channel: {voice_channel.name}')
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


@BOT.command(name="code", aliases=["c"])
@commands.check(ctx_is_lobby)
async def code(ctx, args):
    """
    Used to set a text-channel's name to the name of a game code.

    Codes should be all alpha charactrers, and 6 characters long.

    This should only work in a lobby.
    """

    # TODO: This does not publish an error message when code criteria isn't met

    if is_lobby(ctx.channel.category) and args.isalpha() and len(args) == 6:
        await ctx.channel.edit(name=args)


@BOT.command(name="promote")
@commands.has_permissions(manage_channels=True)
@commands.check(ctx_is_lobby)
async def promote(ctx, user: discord.User):
    """
    Grants a user 'admin' access to a lobby. You must be a current lobby admin to use this command.
    """

    # TODO: This does not publish an error message when the user is not a lobby admin
    # TODO: This does not yet provide a confirmation message

    if is_lobby(ctx.channel.category):
        await initialize_lobby_admin(user, ctx.channel.category)
        # await ctx.channel.edit(name=args)


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
        if ctx_is_lobby(ctx):
            await ctx.send(f'{ctx.author.mention} You do not have access to run this command.')
        else:
            # Delete unauthorized commands that come from outside a lobby
            await ctx.message.delete()
    elif isinstance(error, LocationError):
        await ctx.send(f'{ctx.author.mention} {error.message}')
    else:
        logger.error(
            f'Unknown error. Invocation: {ctx.message.content}. \nError: {error}')

BOT.run(TOKEN)

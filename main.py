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


@BOT.event
async def on_ready():
    """Produces log for when the bot is ready for action"""
    logger.info(f'{BOT.user.name} has connected to Discord!')


@BOT.event
async def on_voice_state_update(member, before, after):
    """
    Handler for automatically managing lobbies

    Create a new lobby when user joins seed_channel.
    New channel will use the same configuration from seed_channel.

    Delete any empty lobbies.
    """

    # Don't do anything if user's channel didn't update
    if before.channel is not after.channel:

        guild = member.guild
        seed_channel = utils.get(guild.voice_channels,
                                 name='Create New Lobby')

        # If user is in the seed channel, create new lobby and move user
        if member.voice is not None:
            if member.voice.channel is seed_channel:
                # User has joined the seed channel
                await initialize_lobby(guild, seed_channel, member)
            else:
                # User is joining an existing lobby
                await initialize_lobby_member(member, member.voice.channel.category)

        # If user left a lobby
        if before.channel is not None and before.channel is not seed_channel:
            # Clear member's roles from last lobby
            await clear_member_lobby_overwrites(member, before.channel.category)

            # If the last lobby is empty, delete it
            if not before.channel.members:
                await delete_empty_lobby(before.channel.category)


async def initialize_lobby_member(member, category):
    """
    Grants a user access to the currently joined lobby.
    Assumes the current lobby exists, and the member is still present in the lobby.
    """

    # Grant read access to text channels
    for text_channel in category.text_channels:
        await text_channel.set_permissions(member, read_messages=True)


async def initialize_lobby_admin(member, category):
    category = member.voice.channel.category

    await category.set_permissions(member, manage_channels=True, mute_members=True)


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


async def delete_empty_lobby(category):
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


@BOT.event
async def on_command_error(ctx, error):
    """Core error handler"""
    if isinstance(error, commands.errors.CheckFailure):
        logger.info(
            f'{ctx.author} attempted to run command: {ctx.message.content}')
        await ctx.send('You do not have the correct role for this command.')
    else:
        logger.error(
            f'Unknown error. Invocation: {ctx.message.content}. \nError: {error}')

BOT.run(TOKEN)

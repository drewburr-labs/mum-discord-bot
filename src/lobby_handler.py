# lobby_handler.py
"""
Handler for automatically creating and deleting lobbies.
"""
from logging import Logger

import discord
from discord import utils
from discord.ext import commands
from .common import Common


class lobby_handler(commands.Cog):
    def __init__(self, bot: commands.Bot, logger: Logger):
        self.bot = bot
        self.logger = logger
        self.text_channel_name = "text-chat"

    @commands.Cog.listener()
    async def on_voice_state_update(
        self,
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState,
    ):
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

            seed_channel = utils.get(guild.voice_channels, name="Create New Lobby")

            # If user joined a channel
            if after.channel is not None:
                if after.channel is seed_channel:
                    # User has joined the seed channel. Create a new lobby.
                    try:
                        await self.initialize_lobby(guild, seed_channel, member)
                    except Exception as e:
                        self.logger.warn('Failed to initialize lobby')
                        self.logger.warn(e)
                        raise e
                elif Common.is_lobby(after.channel.category):
                    # User is joining an existing lobby
                    await self.initialize_lobby_member(member, after.channel.category)

            # If user left a lobby
            if before.channel is not None and Common.is_lobby(before.channel.category):
                # Clear member's permissions from last lobby
                await self.clear_member_lobby_overwrites(
                    member, before.channel.category
                )

                # If the last lobby is empty, delete it
                if not before.channel.members:
                    await self.delete_lobby(before.channel.category)

    async def initialize_lobby(
        self,
        guild: discord.Guild,
        seed_channel: discord.VoiceChannel,
        member: discord.Member,
    ):
        """
        Creates a lobby (category) named after the member.
        Adds a text and voice channel to the category.
        Revokes default read access to the text channel.
        The creating member will be automatically moved into the lobby.
        """

        # Generate a lobby, based on the username
        # Drewburr's Lobby
        category_name = f"{member.display_name}'s Lobby"
        voice_channel_name = "voice chat"

        if seed_channel.category:
            category: discord.CategoryChannel = await seed_channel.category.clone(
                name=category_name
            )
        else:
            category = await seed_channel.guild.create_category_channel(category_name)


        voice_channel: discord.VoiceChannel = await seed_channel.clone(
            name=voice_channel_name
        )
        await voice_channel.move(beginning=True, category=category)
        await self.initialize_lobby_text_channel(category)

        # Move the user to the lobby. Triggers 'on_voice_state_update'
        self.logger.info(
            f"Moving {member.display_name} to channel: {voice_channel.name}"
        )
        await member.edit(voice_channel=voice_channel)

    async def initialize_lobby_text_channel(self, category: discord.CategoryChannel):
        """
        Creates the text channel for a particular lobby.
        Text channel is hidden from users by revoking default read access.
        Retuns the created text channel.
        """
        guild = category.guild
        prefix = self.bot.command_prefix

        text_channel_topic = f"Use {prefix}code to set a game code."

        # Setup overwrites
        default_overwrite = discord.PermissionOverwrite(read_messages=False)

        bot_member = utils.get(guild.members, id=self.bot.user.id)
        bot_role = bot_member.roles[-1]

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False), # Set global deny
            bot_role: discord.PermissionOverwrite(read_messages=True) # Ensure bot keeps permissions
        }

        # Setup text channel
        text_channel = await category.create_text_channel(
            self.text_channel_name, topic=text_channel_topic, overwrites=overwrites
        )

        await self.send_lobby_welcome_message(text_channel)

        return text_channel

    async def initialize_lobby_member(
        self, member: discord.Member, category: discord.CategoryChannel
    ):
        """
        Grants a user access to the currently joined lobby.
        Assumes the current lobby exists, and the member is still present in the lobby.
        """

        # Grant read access to text channels
        for channel in category.text_channels:
            await channel.set_permissions(member, read_messages=True)
            if channel.name == self.text_channel_name:
                await channel.send(f"{member.mention} joined the lobby.")

    # @BOT.command(name="test")
    async def send_lobby_welcome_message(self, text_channel: discord.TextChannel):
        # text_channel = utils.get(ctx.guild.text_channels, name='general')
        prefix = self.bot.command_prefix

        # https://discord.readthedocs.io/en/latest/api.html#embed
        embed_data = {
            "title": "Welcome to the lobby!",
            "description": "Here's some tips to get you started",
            "fields": [
                {
                    "name": f"The {self.text_channel_name}",
                    "value": f"Only members in the lobby's voice chat can see the {self.text_channel_name}. This is your private space to chat and discuss.",
                },
                {
                    "name": "Make it your own!",
                    "value": f"Rename the lobby using the `{prefix}rename` command.",
                },
                {
                    "name": "Limiting members",
                    "value": f"Use the `{prefix}limit` command to change how many members can join the voice channel. Use `0` to remove the limit.",
                },
                {
                    "name": f"The `{prefix}code` command",
                    "value": f"Use the `{prefix}code` command to communicate game codes. Use this command to get the current game code, or set a new one with `{prefix}code ABCXYZ`. This command also has the alias `{prefix}c`.",
                },
            ],
        }

        embed = discord.Embed.from_dict(embed_data)

        await text_channel.send(embeds=[embed])

    async def delete_lobby(self, category):
        """
        Handles the deletion of an existing lobby.
        Assumes lobby still exists.
        """

        channels = category.channels
        self.logger.info(f"Deleting empty category: {category}")

        # Delete all channels
        for channel in channels:
            try:
                self.logger.info("Deleting channel: " + channel.name)
                await channel.delete()
            except Exception as e:
                self.logger.info("Failed to delete lobby channel")
                self.logger.info(e)
                raise e

        # Delete category
        self.logger.info("Deleting category: " + category.name)
        await category.delete()

    async def clear_member_lobby_overwrites(
        self, member: discord.Member, category: discord.CategoryChannel
    ):
        """
        Clears a user's permission overwrites from a lobby.
        Permssion overwrites are those that differ from the category.
        """

        channels = category.channels

        overwrite = discord.PermissionOverwrite()

        # Remove all channel permission overwrites
        for channel in channels:
            await channel.set_permissions(member, overwrite=overwrite)
            if channel.name == self.text_channel_name:
                await channel.send(f"{member.display_name} left the lobby.")


async def setup(bot: commands.Bot, logger):
    await bot.add_cog(lobby_handler(bot, logger))

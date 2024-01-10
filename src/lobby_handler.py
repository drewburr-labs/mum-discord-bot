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
        self.seed_channel_name = "Create New Lobby"

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

        guild = member.guild

        logger_context = {
            "before_category": "",
            "before_channel": "",
            "after_category": "",
            "after_channel": "",
            "guild": guild.name,
            "member": member.name,
        }

        if before.channel:
            logger_context["before_channel"] = before.channel.name
            if before.channel.category:
                logger_context["before_category"] = before.channel.category.name

        if after.channel:
            logger_context["after_channel"] = after.channel.name
            if after.channel.category:
                logger_context["after_category"] = after.channel.category.name

        # Don't do anything if user's channel didn't update
        if before.channel is not after.channel:
            self.logger.debug(f"Member voice state changed. {logger_context}")

            if after.channel is not None:
                seed_channel = after.channel
                self.logger.debug(f"Member joined new voice channel. {logger_context}")

                if after.channel.name.lower() == self.seed_channel_name.lower():
                    self.logger.info(f"Member creating new lobby. {logger_context}")
                    try:
                        await self.initialize_lobby(seed_channel, member)
                    except Exception as e:
                        self.logger.error("Failed to initialize lobby")
                        self.logger.error(f"Exception: {e}")

                elif Common.is_lobby(after.channel.category):
                    self.logger.info(f"Member joined existing lobby. {logger_context}")
                    try:
                        await self.initialize_lobby_member(
                            member, after.channel.category
                        )
                    except Exception as e:
                        self.logger.error(
                            f"Failed to initialize lobby member. {logger_context}"
                        )
                        self.logger.error(f"Exception: {e}")

            if before.channel is not None and Common.is_lobby(before.channel.category):
                self.logger.info(f"Member left lobby. {logger_context}")

                try:
                    await self.remove_lobby_member(member, before.channel.category)
                except Exception as e:
                    self.logger.error(
                        f"Failed to clear member lobby overwrites. {logger_context}"
                    )
                    self.logger.error(f"Exception: {e}")

                try:
                    if not before.channel.members:
                        self.logger.info(f"Deleting empty lobby. {logger_context}")
                        await self.delete_lobby(before.channel.category)
                except Exception as e:
                    self.logger.error(f"Failed to delete empty lobby. {logger_context}")
                    self.logger.error(f"Exception: {e}")

    async def initialize_lobby(
        self, seed_channel: discord.VoiceChannel, member: discord.Member
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
        guild = seed_channel.guild

        self.logger.info(
            f"Creating new lobby ({category_name}) in guild {guild} ({guild.id})"
        )

        if seed_channel.category:
            self.logger.info(f"Cloning seed category. ({category_name})")
            category: discord.CategoryChannel = await seed_channel.category.clone(
                name=category_name
            )
        else:
            self.logger.info(f"Creating lobby category. ({category_name})")
            category = await guild.create_category_channel(category_name)

        voice_channel_kwargs = {
            "name": voice_channel_name,
            "bitrate": seed_channel.bitrate,
            "user_limit": seed_channel.user_limit,
            "video_quality_mode": seed_channel.video_quality_mode,
        }

        voice_channel_settings = {
            "nsfw": seed_channel.nsfw,
            "slowmode_delay": seed_channel.slowmode_delay,
            "rtc_region": seed_channel.rtc_region,
        }

        voice_channel_overwrites = seed_channel.overwrites

        self.logger.info(f"Lobby voice channel arguments: {voice_channel_kwargs}")
        self.logger.info(f"Lobby voice channel settings: {voice_channel_settings}")

        display_overwrites = {
            f"{type(target).name} {target.name}": overwrite.pair()
            for (target, overwrite) in voice_channel_overwrites.items()
        }
        self.logger.info(f"Lobby voice channel overwrites: {display_overwrites}")
        voice_channel_kwargs["overwrites"] = voice_channel_overwrites

        try:
            self.logger.info(f"Creating lobby voice channel. ({voice_channel_name})")
            voice_channel: discord.VoiceChannel = await category.create_voice_channel(
                **voice_channel_kwargs
            )
            await voice_channel.edit(**voice_channel_settings)
        except Exception as e:
            self.logger.error(
                f"Failed to create lobby voice channel. ({category_name})"
            )
            self.logger.error(f"Exception: {e}")

        try:
            self.logger.info(f"Initializing text channel for lobby. ({category_name})")
            await self.initialize_lobby_text_channel(category)
        except Exception as e:
            self.logger.error(f"Failed to create lobby text channel. ({category_name})")
            self.logger.error(f"Exception: {e}")

        try:
            # Triggers 'on_voice_state_update'
            self.logger.info(
                f"Moving {member.name} to lobby voice channel. ({category_name})"
            )
            await member.edit(voice_channel=voice_channel)
        except Exception as e:
            self.logger.error(
                f"Failed to move {member.name} to lobby voice channel. ({category_name})"
            )
            self.logger.error(f"Exception: {e}")

    async def initialize_lobby_text_channel(self, category: discord.CategoryChannel):
        """
        Creates the text channel for a particular lobby.
        Text channel is hidden from users by revoking default read access.
        Retuns the created text channel.
        """
        guild = category.guild
        prefix = self.bot.command_prefix

        text_channel_topic = f"Use {prefix}code to set a game code."

        bot_member = utils.get(guild.members, id=self.bot.user.id)
        bot_role = bot_member.roles[-1]

        overwrites = {}

        # Default global deny
        overwrites[guild.default_role] = discord.PermissionOverwrite(read_messages=False)

        for target, overwrite in category.overwrites.items():
            if overwrite.read_messages:
                overwrites[target] = discord.PermissionOverwrite(read_messages=True)

        # Ensure bot keeps read permissions
        overwrites[bot_role] = discord.PermissionOverwrite(read_messages=True)

        self.logger.info(f"Creating lobby text channel. ({category.name})")
        text_channel = await category.create_text_channel(
            self.text_channel_name, topic=text_channel_topic, overwrites=overwrites
        )

        self.logger.info(f"Sending lobby welcome message. ({category.name})")
        await self.send_lobby_welcome_message(text_channel)

        return text_channel

    async def initialize_lobby_member(
        self, member: discord.Member, category: discord.CategoryChannel
    ):
        """
        Grant a member access to the currently joined lobby.
        Assumes the current lobby exists, and the member is still present in the lobby.
        """

        # Grant read access to text channels
        for channel in category.text_channels:
            self.logger.info(
                f"Granting member read access to text channel. ({category.name})"
            )
            await channel.set_permissions(member, read_messages=True)
            if channel.name == self.text_channel_name:
                self.logger.info(
                    f"Sending member join notification message. ({category.name})"
                )
                await channel.send(f"{member.display_name} joined the lobby.")

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

    async def delete_lobby(self, category: discord.CategoryChannel):
        """
        Handles the deletion of an existing lobby.
        Assumes lobby still exists.
        """

        channels = category.channels
        self.logger.info(f"Deleting empty category. ({category})")

        # Delete all channels
        for channel in channels:
            try:
                self.logger.info(f"Deleting {channel.type} channel ({channel})")
                await channel.delete()
            except Exception as e:
                self.logger.info(f"Failed to delete lobby channel. ({category.name})")
                self.logger.info(f"Exception: {e}")
                raise e

        # Delete category
        self.logger.info(f"Deleting category. {category.name}")
        await category.delete()

    async def remove_lobby_member(
        self, member: discord.Member, category: discord.CategoryChannel
    ):
        """
        Clears a user's permission overwrites from a lobby.
        Permssion overwrites are those that differ from the category.
        """

        channels = category.text_channels
        overwrite = discord.PermissionOverwrite()

        # Remove all channel permission overwrites
        self.logger.info(f"Removing lobby text channel overwrites. ({member.name})")
        for channel in channels:
            try:
                await channel.set_permissions(member, overwrite=overwrite)
                if channel.name == self.text_channel_name:
                    self.logger.info(
                        f"Sending member leave notification message for {member.name} ({category.name})"
                    )
                    await channel.send(f"{member.display_name} left the lobby.")
            except Exception as e:
                self.logger.error(
                    f"Failed to remove permissions on channel {channel.name} ({category.name})"
                )
                self.logger.error(f"Exception: {e}")


async def setup(bot: commands.Bot, logger):
    await bot.add_cog(lobby_handler(bot, logger))

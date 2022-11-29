# lobby_commands.py
"""
lobby_commands is used to provide all lobby commands.
"""

import discord
from discord import app_commands
from discord.ext import commands

from typing import Optional

from .common import Common

Common = Common()


class lobby_commands(commands.Cog):
    def __init__(self, bot, logger, APP_DIR):
        self.bot: commands.Bot = bot
        self.logger = logger
        self._APP_DIR = APP_DIR
        self.code_prefix = "Game code: "

    # @client.tree.command()
    # @app_commands.
    @app_commands.command(name="code")
    @app_commands.describe(value="The game code to set.")
    @app_commands.check(Common.ctx_is_lobby)
    async def code(self, interaction: discord.Interaction, value: Optional[str]):
        # Code will be re-messaged to the channel with a mention to the text chat.
        # The channel topic will be updated to the game code.
        """
        Used to get or set a game code.
        """
        response = interaction.response
        topic = interaction.channel.topic

        if value is None:
            # User is requesting the game code
            if not topic.startswith(self.code_prefix):
                await response.send_message(
                    f"A game code hasn't been set yet! Use `/code` to set one.")
            else:
                await response.send_message(f"{interaction.user.mention} The game code is `{topic.removeprefix(self.code_prefix)}`")

        else:
            self.logger.info(
                f"Updating code for lobby: '{interaction.channel.category}' - '{value}'")
            await response.send_message(f"{interaction.channel.mention} The game code was changed to `{value}`")
            await interaction.channel.edit(topic=self.code_prefix + value)

    @app_commands.command(name="rename")
    @app_commands.describe(name="New lobby name.")
    @app_commands.check(Common.ctx_is_lobby)
    @app_commands.checks.cooldown(rate=2, per=600, key=lambda i: i.channel.category_id)
    async def rename(self, interaction: discord.Interaction, name: str):
        """
        Rename the current lobby.
        Usage: /rename <New name>
        Lobbies can be renamed twice every 10 minutes.
        """
        new_name = f"{name} lobby".lower()
        category = interaction.channel.category
        self.logger.info(f"Renaming '{category.name}' to '{new_name}")

        await category.edit(name=new_name)
        await interaction.response.send_message(f'Lobby renamed to `{new_name}`')

    @app_commands.command(name="limit")
    @app_commands.describe(value="User limit. Use '0' to remove limit.")
    @app_commands.check(Common.ctx_is_lobby)
    async def limit(self, interaction: discord.Interaction, value: int):
        """
        Change the lobby's user limit.
        Usage: /limit <0-99>
        """
        if value > 99:
            value = 99

        # Ensure user is in a voice channel
        voice_state = interaction.user.voice
        if voice_state:
            await voice_state.channel.edit(user_limit=value)
            await interaction.response.send_message(
                f"Set channel limit to {value}")
        else:
            await interaction.response.send_message(
                "Must be in a voice channel to use this command.")


async def setup(bot: commands.Bot, logger, APP_DIR):
    bot = bot
    await bot.add_cog(lobby_commands(bot, logger, APP_DIR))

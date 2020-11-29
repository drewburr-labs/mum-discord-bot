# common.py
"""
Common functions, methods, and classes to be used globally
"""

import discord


class Common():
    def __init__(self, bot):
        global guild

    def set_guild(bot):
        global guild
        guild = bot.guilds[0]

    # Define custom exception
    class UserError(discord.ext.commands.CommandError):
        """
        A command was run incorrectly, and the user should be told why.
        Example: User executes a lobby-specific command in #general

        Attributes:
            message -- Error message to send to chat, as a reply.
        """

        def __init__(self, message):
            self.message = message

    @staticmethod
    def is_lobby(category):
        """
        Returns True (bool) if a category is a lobby.
        """

        if category.name.endswith("Lobby"):
            return True
        else:
            return False

    def ctx_is_lobby(self, ctx):
        """
        Checks if a message was sent from a lobby's text channel.
        Raises UserError if channel is not a lobby.
        """
        if self.is_lobby(ctx.channel.category):
            return True
        else:
            raise self.UserError('That command can only be used in a lobby.')

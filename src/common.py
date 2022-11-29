# common.py
"""
Common functions, methods, and classes to be used globally
"""

import discord


class Common():
    def __init__(self):
        pass

    class GenericError(discord.app_commands.AppCommandError):
        """
        Base error class, allows messages to be stored.
        """

        def __init__(self, message):
            self.message = message

    # Define custom exception
    class UserError(GenericError):
        """
        An error occurred, and the user should be told why.
        Example: User executes a lobby-specific command in #general
        """

    class AdminError(GenericError):
        """
        An error occurred, and the server admin(s) should be informed.
        """

    class SilentError(GenericError):
        """
        An error occurred, and the error message should not be sent to Discord.
        """

    @staticmethod
    def is_lobby(category: discord.CategoryChannel):
        """
        Returns True (bool) if a category is a lobby.
        """

        if category.name.lower().endswith("lobby"):
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

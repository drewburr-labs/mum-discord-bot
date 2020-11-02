# rule_suggestions.py
"""
"""

from dotenv import load_dotenv
from discord.ext import tasks, commands
from discord import utils
import discord


class rule_suggestions(commands.Cog):
    def __init__(self, bot, logger):
        self.bot = bot
        self.logger = logger
        self.channel = "rule-suggestions"

    # https://discordpy.readthedocs.io/en/latest/api.html#discord.on_message
    @commands.Cog.listener(name="on_message")
    async def repost_rule(self, message):
        """
        Deletes and reposts messages in {self.channel}

        Logs messages and author to bot-logs
        """

        if message.channel.name == self.channel and not message.author.bot:
            await message.delete()
            repost_message = await message.channel.send(message.content)

            yes_emoji = utils.get(message.guild.emojis, name="yes")
            no_emoji = utils.get(message.guild.emojis, name="no")

            await repost_message.add_reaction(yes_emoji)
            await repost_message.add_reaction(no_emoji)

            admin_logger = self.bot.get_cog('admin_logging')
            await admin_logger.bot_log(message.guild,
                                       f"{message.author} added a rule suggestion:\n{message.content}")


def setup(bot, logger):
    bot.add_cog(rule_suggestions(bot, logger))

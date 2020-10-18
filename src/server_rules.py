# server_rules.py
"""
server_rules is used to push roles to the server.

It's also responsible for assigning the Member role, which grants access to the server.
"""

from dotenv import load_dotenv
from discord.ext import tasks, commands
from discord import utils
import discord


class server_rules(commands.Cog):
    def __init__(self, bot, logger):
        self.bot = bot
        self.logger = logger
        self.category = None  # The expected category for each stat channel
        self.channel_name = "rules"

        self.rules_list = [
            {
                "title": "Server Rules",
                "description": "These rules are meant to serve as fallback resources for moderators. We trust the community, and will refer to these rules as guidelines unless escalation is required.",
                "fields":
                [
                    {
                        "name": "Follow Discord Guidelines and ToS",
                        "value": [
                            "- Discord Guidelines: https://discordapp.com/guidelines",
                            "- Discord Terms of Service: https://discordapp.com/terms"
                        ]
                    },
                    {
                        "name": "Content",
                        "value": [
                            "- We do not allow NSFW content. Admins may call out an inappropriate topic, please respect this.",
                            "- Spamming is not allowed, especially '@' spamming. No one wants to see that.",
                            "- Self-advertising is not allowed without former permission."
                        ]
                    },
                    {
                        "name": "Character",
                        "value": [
                            "- Golden rule. Respect your fellow members."
                        ]
                    },
                    {
                        "name": "Follow channel topics",
                        "value": [
                            "- Try to follow channel topics when possible.",
                            "- Please keep server codes in the lobby text channels."
                        ]
                    },
                    {
                        "name": "Respect admins",
                        "value": [
                            "- If you are not an admin, do not be an admin.",
                            "- If you have an issue with an admin, please DM drewburr."
                        ]
                    }
                ]
            },
            {
                "title": "Lobby Rules",
                "description": "Server rules also apply to the Lobby rules. This is more or less the baseline of what can be expected from lobby members.",
                "fields":
                [
                    {
                        "name": "Respect your fellow players",
                        "value": [
                            "- Do not shout or insult members if you are killed or lose a game.",
                            "- If you are asked to leave a lobby, do so kindly."
                        ]
                    },
                    {
                        "name": "Gameplay etiquette",
                        "value": [
                            "- Do not shout or insult members if you are killed or lose a game.",
                            "- If you are joining a new lobby, understand a game may already be in progress.",
                            "- Do not throw the game. (Exposing your fellow imposter(s), sharing information between rounds, talking when dead.)",
                            "- Don't stall the game because you're being salty.",
                            "- No hacking."
                        ]
                    },
                    {
                        "name": "Game codes",
                        "value": "- Please do not share game codes in #general. Every lobby has a text channel for this purpose."
                    }
                ]
            }
        ]

    @commands.command(name="refresh-rules")
    async def refresh_rules_channel(self, ctx):
        """
        Sets up the rules channel to ensure the messages are up to date.
        """

        rules_channel = utils.get(
            ctx.guild.text_channels, name=self.channel_name)

        if ctx.channel is rules_channel:
            print("Updating rules")
            # Delete all messages in the channel
            await rules_channel.purge()

            # Publish new messages
            for data in self.rules_list:
                print(data)
                await self.send_rules_message(rules_channel, data)

    async def send_rules_message(self, channel, message_data):
        """
        Responsible for formatting and sending the rules messages.
        """

        # values = list()

        for field in message_data['fields']:
            value = field.get('value')

            if isinstance(value, list):
                field['value'] = '\n'.join(value)

        embed = discord.Embed.from_dict(message_data)
        message = await channel.send(embed=embed)


def setup(bot, logger):
    bot.add_cog(server_rules(bot, logger))

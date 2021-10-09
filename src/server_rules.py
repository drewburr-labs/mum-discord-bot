# server_rules.py
"""
server_rules is used to push roles to the server.

It's also responsible for assigning the Member role, which grants access to the server.
"""

from disnake.ext import commands
from disnake import utils
import disnake
import asyncio


class server_rules(commands.Cog):
    def __init__(self, bot, logger):
        self.bot = bot
        self.logger = logger
        self.category = None  # The expected category for each stat channel
        self.channel_name = "rules"
        self.member_role = "Member"
        self.accept_msg = "I have read and accept the rules"

        self.rules_list = [
            {
                "title": "Server Rules",
                "description": "Breaking the rules will result in a kick or ban. If you believe a member has broken one of these rules, please let a member of the Mod team know.",
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
                            "- Spamming is not allowed. No one wants to see that.",
                            "- Self-advertising is not allowed without former permission.",
                            "- Posting links to streams and self-made content is welcome."
                        ]
                    },
                    {
                        "name": "Character",
                        "value": [
                            "- Golden rule. Respect your fellow members.",
                            "- Do not shout at or insult members.",
                            "- Comments that are racist, sexist, or hold prejudice will result in an immediate ban.",
                            "- If you are asked to leave a lobby, do so kindly."
                        ]
                    },
                    {
                        "name": "Follow channel topics",
                        "value": [
                            "- Try to follow channel topics when possible.",
                            "- Please keep game codes in the lobby text channels."
                        ]
                    },
                    {
                        "name": "Gameplay etiquette",
                        "value": [
                            "- Don't stall the game because you're being salty.",
                            "- No hacking."
                        ]
                    },
                    {
                        "name": "Admins",
                        "value": [
                            "- If you are not an admin, do not be an admin.",
                            "- If you have an issue with an admin, please DM drewburr."
                        ]
                    },
                ]
            },
        ]

    @commands.has_role('Mod')
    @commands.command(name="refresh-rules")
    async def refresh_rules_channel(self, ctx):
        """
        Sets up the rules channel to ensure the messages are up to date.
        """

        rules_channel = utils.get(
            ctx.guild.text_channels, name=self.channel_name)

        if ctx.channel is rules_channel:
            self.logger.info("Updating rules")
            # Delete all messages in the channel
            await rules_channel.purge()

            # Publish new messages
            for data in self.rules_list:
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

        embed = disnake.Embed.from_dict(message_data)
        await channel.send(embed=embed)

    # @commands.Cog.listener(name="on_member_update")
    # async def on_member_update(self, before, after):
    #     print(after)
    #     print(before.pending, after.pending)
    #     member_role = utils.get(member.guild.roles, name=self.member_role)
    #     await member.add_roles(member_role)


def setup(bot, logger):
    bot.add_cog(server_rules(bot, logger))

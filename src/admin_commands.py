# admin_commands.py
"""
admin_commands is used to run all admin commands. These must be executed by a moderator.
"""

from dotenv import load_dotenv
from discord.ext import commands
from discord import utils
import discord

import asyncio


class admin_commands(commands.Cog):
    def __init__(self, bot, logger):
        self.bot = bot
        self.logger = logger
        self.channel_name = 'admin-commands'

    @commands.has_role('Mod')
    @commands.command(name="softban")
    async def ban(self, ctx, softban_member: discord.Member, *, reason):
        """
        Starts a vote to softban a user.

        Softbanned users are given the 'softban' role, and are muted and deafened.
        """
        if ctx.message.channel.name != self.channel_name:
            await ctx.message.delete()
            raise Exception("Softban command was ran from an invalid channel.")

        softban_role = 'Softban'

        emoji_data = {
            'yes': None,
            'no': None,
        }

        embed_data = {
            "title": "Softban vote started!",
            "description": f"{ctx.author.mention} has started a vote to softban {softban_member.mention}. An approval is required from another mod.\n\nReason: {reason}",
        }

        # Get emoji data for later use
        for name in emoji_data:
            emoji = utils.get(ctx.guild.emojis, name=name)
            emoji_data[name] = emoji

        embed = discord.Embed.from_dict(embed_data)
        message = await ctx.channel.send(embed=embed)

        for emoji in emoji_data.values():
            await message.add_reaction(emoji)

        admin_logger = self.bot.get_cog('admin_logging')
        await admin_logger.bot_log(ctx.guild, f"{ctx.author.display_name} has initiated a vote to softban {softban_member.display_name}. Reason: {reason}.")

        def approver_not_author(reaction, user):
            if user.name is ctx.author.name:
                return False

            return True

        # Wait for the vote results
        reaction = None
        user = None
        try:
            reaction, user = await self.bot.wait_for('reaction_add', check=approver_not_author, timeout=600)
        except asyncio.TimeoutError:
            await admin_logger.bot_log(ctx.guild, f"{softban_member.display_name} was not softbanned. Timed out.")

        # Handle the vote results
        if reaction and user:
            if reaction.emoji.name == 'yes':
                softban_role = utils.get(
                    ctx.guild.roles, name=softban_role)

                await softban_member.edit(roles=[softban_role])
                try:
                    await softban_member.edit(mute=True, deafen=True)
                except:
                    pass

                await admin_logger.bot_log(ctx.guild, f"{softban_member.display_name} ({softban_member.name}#{softban_member.discriminator}) was softbanned. Requested by: {ctx.author.display_name}. Approved by: {user.display_name}.")

            elif reaction.emoji.name == 'no':
                await admin_logger.bot_log(ctx.guild, f"{softban_member.display_name} was not softbanned. Denied by: {user.display_name}.")


def setup(bot, logger):
    bot.add_cog(admin_commands(bot, logger))
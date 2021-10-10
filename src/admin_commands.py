# admin_commands.py
"""
admin_commands is used to run all admin commands. These must be executed by a moderator.
"""

from disnake.ext import commands
from disnake import utils
import disnake

from .common import Common


class admin_commands(commands.Cog):
    def __init__(self, bot, logger):
        self.bot = bot
        self.logger = logger

        self.softban_role_name = 'Softban'
        self.member_role_name = 'Member'
        self.admin_command_channel_name = 'admin-commands'

    def ctx_is_admin_commands(self, ctx):
        if ctx.channel.name == self.admin_command_channel_name:
            return True
        else:
            return False

    @commands.has_role('Mod')
    @commands.command(name="member-roles")
    async def member_roles(self, ctx):
        """
        Ensures all server members have the Member role
        """
        member_role = utils.get(ctx.guild.roles, name=self.member_role_name)
        softban_role = utils.get(ctx.guild.roles, name=self.softban_role_name)

        total_changes = 0

        for member in ctx.guild.members:
            if member_role not in member.roles and softban_role not in member.roles and not member.bot:
                await member.add_roles(member_role)
                total_changes += 1

        await ctx.send(f'Added the `{member_role.name}` role to {total_changes} members.')

    @commands.has_role('Mod')
    @commands.command(name="softban")
    # @commands.check(ctx_is_admin_commands)
    async def softban(self, ctx, softban_member: disnake.Member = None, *, reason=None):
        """
        Starts a vote to softban a user.

        Softbanned users are given the 'softban' role, and are muted and deafened.
        """
        # Ensure command is ran from admin channel
        if not self.ctx_is_admin_commands(ctx):
            await ctx.message.delete()
            raise Common.AdminError(
                f'!softban must be run from the {self.admin_command_channel_name} channel')

        if not softban_member or not reason:
            raise Common.UserError(
                'Usage: `!softban drewburr for not being awesome.`')

        admin_logger = self.bot.get_cog('admin_logging')
        await admin_logger.bot_log(ctx.guild, f"{ctx.author.display_name} has softbanned {softban_member.display_name}. Reason: {reason}")

        member_role = utils.get(ctx.guild.roles, name=self.member_role_name)
        softban_role = utils.get(ctx.guild.roles, name=self.softban_role_name)

        await softban_member.add_roles(softban_role)
        await softban_member.remove_roles(member_role)

        if softban_member.voice:
            # Disconnect user from voice chat
            await softban_member.move_to(None)


def setup(bot, logger):
    bot.add_cog(admin_commands(bot, logger))

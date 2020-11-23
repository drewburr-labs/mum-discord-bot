# lobby_commands.py
"""
lobby_commands is used to provide all lobby commands.
"""

from discord.ext import commands
from discord import utils
import discord

import asyncio

from .common import Common

Common = Common()


class lobby_commands(commands.Cog):
    def __init__(self, bot, logger, APP_DIR):
        self.bot = bot
        self.logger = logger
        self._APP_DIR = APP_DIR

    @commands.command(name="code", aliases=["c"])
    @commands.check(Common.ctx_is_lobby)
    async def code(self, ctx, args=None):
        # Code will be re-messaged to the channel with a mention to the text chat.
        # The channel topic will be updated to the game code.
        """
        Used to recieve or communicate a game code to the current lobby.
        """

        category = ctx.channel.category

        if args is None:
            # User is requesting the game code
            if ctx.channel.topic is None:
                await ctx.send(
                    f"A game code hasn't been set yet! Use `{ctx.prefix}code` to set one.")
            else:
                await ctx.send(f"{ctx.author.mention} The game code is `{ctx.channel.topic}`")

        elif Common.is_lobby(category):
            self.logger.info(
                f"Updating code for category: '{category}' - {args}")
            await ctx.send(f"{ctx.channel.mention} The game code is `{args}`")

            await ctx.channel.edit(topic=args)

        else:
            self.logger.info(f"Game code did not meet requirements: {args}")

    @commands.command(name="map")
    @commands.check(Common.ctx_is_lobby)
    async def map(self, ctx, args=None):
        """
        Used to get an Among Us map.
        """

        maps_path = self._APP_DIR + '/maps/'
        maps = {
            'mira': 'Mira.png',
            'polus': 'Polus.png',
            'skeld': 'Skeld.jpg'
        }
        emoji_map = {
            '🚀': 'skeld',
            '✈️': 'mira',
            '❄️': 'polus',
        }
        user = None  # Pylance (reportUnboundVariable)

        # Create the request message
        request_msg = 'Select a map by reacting to this message.'
        for emoji, name in emoji_map.items():
            request_msg += f'\n{emoji} - {name.capitalize()}'

        if args is None:
            message = await ctx.send(request_msg)
            for emoji in emoji_map:
                await message.add_reaction(emoji)

            # Reaction must not be from the bot, message must be the one just sent, and emoji must be valid
            def check(reaction, user):
                return user != message.author and reaction.message.id == message.id and reaction.emoji in emoji_map

            reaction, user = await self.bot.wait_for('reaction_add', check=check, timeout=60)
            map_image = maps.get(emoji_map[reaction.emoji])
        else:
            map_image = maps.get(args.lower())
            # Run the function again to print message
            # Will throw a TypeError below
            if map_image is None:
                await map(ctx)

        try:
            with open(maps_path + map_image, 'rb') as image:
                fp = discord.File(image)
                await ctx.send(file=fp)
                self.logger.info(
                    f'Uploaded map {map_image} for {user.display_name}.')
        except TypeError:
            pass

    @commands.command(name="mapvote")
    @commands.check(Common.ctx_is_lobby)
    async def mapvote(self, ctx, args=None):
        """
        Used to vote on which Among Us map to play.
        """
        votetime_min = 1
        emoji_map = {
            '🚀': 'skeld',
            '✈️': 'mira',
            '❄️': 'polus',
        }

        # Create the request message
        request_msg = f'Vote for a map by reacting to this message.\nThe poll will close in {votetime_min} minute(s).'
        for emoji, name in emoji_map.items():
            request_msg += f'\n{emoji} - {name.capitalize()}'

        message = await ctx.send(request_msg)
        for emoji in emoji_map:
            await message.add_reaction(emoji)

        await asyncio.sleep(votetime_min * 60)

        cache_message = discord.utils.get(
            ctx.bot.cached_messages, id=message.id)

        votes = dict()
        for reaction in cache_message.reactions:
            emoji_name = emoji_map.get(reaction.emoji)
            vote_count = reaction.count
            vote_text = f'{reaction.emoji} {emoji_name.capitalize()}'

            if emoji_name is not None:
                votes[vote_text] = vote_count

        description = str()
        for item in votes:
            description += f'{item} - {votes[item]}\n'

        embed_data = {
            'title': 'Mapvote Results',
            'description': description
        }

        embed = discord.Embed.from_dict(embed_data)
        await ctx.channel.send(embed=embed)

    @commands.command(name="rename")
    @commands.check(Common.ctx_is_lobby)
    async def rename(self, ctx, *, args=None):
        """
        Rename the current lobby.
        Usage: !rename <New name>
        Lobbies can be renamed twice every 10 minutes.
        """

        if args:
            category = ctx.channel.category
            await category.edit(name=f"{args} Lobby")
        else:
            raise Common.UserError(
                "This command requires an name. Ex: `!rename New lobby name`")

    @commands.command(name="limit")
    @commands.check(Common.ctx_is_lobby)
    async def limit(self, ctx, args='None'):
        """
        Change the lobby's user limit. Use '0' to remove the limit.
        Usage: !limit <0-99>
        """

        try:
            user_limit = int(args)

            if user_limit <= 99 and user_limit >= 0:
                voice_state = ctx.author.voice

                # Ensure user is in a voice channel
                if voice_state:
                    await voice_state.channel.edit(user_limit=user_limit)

            else:
                raise ValueError

        except ValueError:
            raise Common.UserError(
                "This command requires a value of 0-99. Example: `!limit 10`")

    @commands.command(name="votekick")
    @commands.check(Common.ctx_is_lobby)
    async def votekick(self, ctx, sus_member: discord.Member, *, reason):
        """
        Starts a vote to kick a member from a lobby.

        Member will be unable to rejoin the lobby if kicked.
        """
        # This will throw an 'Unknown Channel' error if the kicked user is the last channel member.
        voice_channel = ctx.author.voice.channel
        member_count = len(voice_channel.members)

        emoji_data = {
            'yes': None,
            'no': None,
        }

        member_names = list()
        for member in voice_channel.members:
            member_names.append(member.display_name)

        name_list = '\n'.join(member_names)

        # Majority, rounded up.
        vote_limit = round(member_count/2)

        embed_data = {
            "title": "Votekick started!",
            "description": f"{ctx.author.mention} has started a vote to kick {sus_member.mention} from the lobby. If kicked, {sus_member.display_name} will be unable to rejoin the lobby.\n\nReason: {reason}",
            "fields":
            [
                {
                    "name": "Votes required to kick",
                    "value": f"{vote_limit}",
                },
                {
                    "name": "Members allowed to vote",
                    "value": f"{name_list}",
                },
            ]
        }

        for name in emoji_data:
            emoji = utils.get(ctx.guild.emojis, name=name)
            emoji_data[name] = emoji

        embed = discord.Embed.from_dict(embed_data)
        message = await ctx.channel.send(embed=embed)

        admin_logger = self.bot.get_cog('admin_logging')
        await admin_logger.bot_log(ctx.guild, f"{ctx.author.display_name} has initiated a vote to kick {sus_member.display_name} from {ctx.channel.category}. Reason: {reason}. Votes required: {vote_limit}.")

        for emoji in emoji_data.values():
            await message.add_reaction(emoji)

        yes_count = 0

        def check_kick(reaction, user):
            """
            Checks if the vote count has exceeded the vote limit.

            Returns True if the user is eligible for kicking.
            """
            nonlocal yes_count
            if user != message.author and reaction.message.id == message.id and reaction.emoji is emoji_data['yes']:
                cache_message = discord.utils.get(
                    ctx.bot.cached_messages, id=message.id)
                reactions = cache_message.reactions

                embed = cache_message.embeds[0].to_dict()

                valid_users = embed['fields'][1]['value'].splitlines()

                if user.display_name in valid_users:
                    for reaction in reactions:
                        # Must be greater than vote limit to account for the bot's reaction
                        if reaction.emoji.name == 'yes':
                            yes_count += 1
                            if yes_count >= vote_limit:
                                return True
            return False

        member_kicked = True
        try:
            await self.bot.wait_for('reaction_add', check=check_kick, timeout=120)
        except asyncio.TimeoutError:
            member_kicked = False

        # Disconnect the user and deny the ability to reconnect
        if member_kicked:
            await sus_member.move_to(ctx.guild.afk_channel, reason="Kicked from Lobby")

            # Update user's permission overwrites
            overwrite = discord.PermissionOverwrite(connect=False)

            # Execute this to ensure there's enough time before updating permissions
            await asyncio.sleep(1)

            await voice_channel.set_permissions(sus_member, overwrite=overwrite)

        # Cache the current state of the message
        cache_message = discord.utils.get(
            ctx.bot.cached_messages, id=message.id)

        reactions = cache_message.reactions
        embed = cache_message.embeds[0].to_dict()
        valid_users = embed['fields'][1]['value'].splitlines()

        vote_data = {
            'yes': [],
            'no': []
        }

        # Get the results of the vote
        for reaction in reactions:
            emoji_name = reaction.emoji.name
            data = vote_data.get(emoji_name)
            # If emoji_name is 'yes' or 'no'
            if data is not None:
                users = await reaction.users().flatten()
                for user in users:
                    if user.display_name in valid_users:
                        # Add user to the list
                        data.append(user.display_name)
                        # Update vote data
                        vote_data[emoji_name] = data

        yes_count = len(vote_data['yes'])
        yes_users = '\n'.join(vote_data['yes'])
        if not yes_users:
            yes_users = "None"

        no_count = len(vote_data['no'])
        no_users = '\n'.join(vote_data['no'])
        if not no_users:
            no_users = "None"

        if member_kicked:
            description = f"{sus_member.display_name} has been kicked from {ctx.channel.category}.\nReason: {reason}\nVotes needed: {vote_limit}"
        else:
            description = f"{sus_member.display_name} was **not** kicked from {ctx.channel.category}.\nReason: {reason}\nVotes needed: {vote_limit}"

        log_embed_data = {
            "title": "Votekick results",
            "description": description,
            "fields": [
                {
                    "name": f"Voted yes ({yes_count})",
                    "value": f"{yes_users}"
                },
                {
                    "name": f"Voted no ({no_count})",
                    "value": f"{no_users}"
                },
            ]
        }

        log_embed = discord.Embed.from_dict(log_embed_data)

        await admin_logger.bot_log(ctx.guild, embed=log_embed)


def setup(bot, logger, APP_DIR):
    bot.add_cog(lobby_commands(bot, logger, APP_DIR))

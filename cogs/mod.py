import discord
from discord.ext import commands
from cogs.utils.modUtils import Mod_Utils
from sqlite3 import OperationalError
from cogs.utils.loggerEntry import *

import asyncio
import datetime
import random
import json
import re
import math


def is_user():
    def pred(ctx):
        cmd = str(ctx.command)
        author = ctx.author
        user_roles = [r.id for r in author.roles]

        with open('./jsons/permissions.json') as f:
            perms = json.load(f)

        try:
            cmd_roles = perms[cmd]
        except KeyError:
            """
            If the command is not in the JSON file, assume everyone has access,
            including standard members. (This is useful for fun commands, where
            they do not modify the server in any way, and saves you time by not
            writing them in the file.)
            """
            return True
        else:
            """
            ELse if the command *is* in the JSON file, and there is no blacklisted
            roles specified, everyone who can access the bot in general (i.e.
            moderators, etc.) can use it. But still not normal users. (This is good
            for commands like ban, unban, or just cummands that you want anyone who
            has access to the bot to use, but not *everyone* in the *server*.)
            """
            # Check if the user is a moderator:
            for r_id in user_roles:
                if r_id in perms['moderator_role_ids']:
                    for r_id in user_roles:
                        if r_id in cmd_roles:
                            perms = f'"USE_{cmd.upper()}"'
                            raise MissingPermissions(
                                perms
                            )
                    return True # If we went through the loop and didn't find and viOwOlatiOwOns
            raise NoAccess(f"You are not authorized to use `{ctx.me.name}` at this time.")
    return commands.check(pred)


class MissingPermissions(Exception):
    def __init__(self, msg):
        super().__init__("You are missing the permission(s): {}.".format(msg))


class NoAccess(Exception):
    def __init__(self, msg):
        super().__init__("No access: {}".format(msg))


class Moderator(commands.Cog, Mod_Utils):
    def __init__(self, bot):
        super().__init__(bot)
        self.bot = bot
        self.pagination_amt = 5
        self.muted_role = self.get_role("muted_role")
        self.kenneled_role = self.get_role("kenneled_role")
        self.kenneled_channel = self.get_channel("kenneled_channel")

    @commands.command(description='Run SQL queries.')
    @commands.has_permissions(administrator=True)
    async def sqlrun(self, ctx, *, query):
        resp = await self.db.get(
            query
        )
        await ctx.send("Response: {}".format(resp))

    @commands.command(description='Change config settings.')
    @is_user()
    async def updateprefix(self, ctx, prefix):
        with open('./jsons/prefixes.json') as f:
            prefixes = json.load(f)

        prefixes[str(ctx.guild.id)] = prefix

        with open('./jsons/prefixes.json', 'w') as f:
            json.dump(prefixes, f, indent=4)

    @commands.command(description='Add/remove user roles.')
    @is_user()
    async def role(self, ctx, user: discord.Member, *, roles: commands.Greedy[discord.Role]):
        """ Adds or removes roles specified to a user. """
        author = ctx.author
        if isinstance(roles, list):
            for role in roles:
                try:
                    await self._edit_roles(ctx, role, user)
                except discord.Forbidden:
                    await ctx.send(f"Could not add the `{role.name}` role to `{author.name}`. "
                    "Please check to see that I have permissions and that the role "
                    "is not above me.")
        else:
            try:
                await self._edit_roles(ctx, roles, user)
            except discord.Forbidden:
                await ctx.send(f"Could not add the `{role.name}` role to `{author.name}`. "
                "Please check to see that I have permissions and that the role "
                "is not above me.")

    @commands.command(description='Mute a user. Removes all roles')
    @is_user()
    async def mute(self, ctx, user: discord.Member, *, reason = "No reason given."):
        """ Removes all roles from user and adds muted role """
        author = ctx.author
        guild = ctx.guild
        channel = ctx.channel
        if await self.is_muted(user):
            await ctx.send(
                "That user is already muted!"
            )
        else:
            muted = guild.get_role(self.muted_role)
            user_roles = [
                r for r in user.roles if r < guild.me.top_role 
                and not (r.is_default() or r.managed)
            ]
            if len(user_roles) > 1:
                await user.remove_roles(*user_roles, reason="Muting user...")
            await self.add_muted(user, user_roles)
            await user.add_roles(muted, reason=reason)
            await channel.send('User muted! Set a reminder to remind you to unmute!')
            identifier = await self.generate_id()
            await self.log_warn(identifier, user, author, f"(Autowarn: type `mute`) - {reason}")

            try:
                await user.send(
                    f"You were muted in **`{guild}`** for **`{reason}`**"
                )
            except discord.Forbidden:
                pass

            logged_entry = f"{author.mention} Muted {user.mention} for {reason}"
            await self.log_entry(
                ctx,
                text=logged_entry,
                entry_type=Mute,
                user=user
            )

    @commands.command(description='Kennel a user.')
    async def kennel(self, ctx, user: discord.Member, *, reason="No reason given."):
        """ Removes all roles from user and adds kennel role """
        author = ctx.author
        guild = ctx.guild
        channel = ctx.channel
        if await self.is_kenneled(user):
            await ctx.send(
                "That user is already kenneled!"
            )
        else:
            kenneled = guild.get_role(self.kenneled_role)
            user_roles = [
                r for r in user.roles if r < guild.me.top_role 
                and not (r.is_default() or r.managed)
            ]
            if len(user_roles) > 1:
                await user.remove_roles(*user_roles, reason="Kenneling user...")
            await self.add_kenneled(user, user_roles)
            await user.add_roles(kenneled, reason=reason)
            await channel.send('User kenneled! Set a reminder to remind you to unmute!')
            identifier = await self.generate_id()
            await self.log_warn(identifier, user, author, f"(Autowarn: type `kennel`) - {reason}")

            try:
                await user.send(
                    f"You were kenneled in **`{guild}`** for **`{reason}`**\n"
                    f"Please check out the **<#{self.kenneled_channel}>** for more information."
                )
            except discord.Forbidden:
                pass

            logged_entry = f"{author.mention} Kenneled {user.mention} for {reason}"
            await self.log_entry(
                ctx,
                title=logged_entry,
                entry_type=Kennel,
                user=user
            )

    @commands.command(description='Unmute a user and return all of their roles.')
    @is_user()
    async def unmute(self, ctx, user: discord.Member, *, reason='No reason given.'):
        """ Adds all roles back to user and unmutes them. """
        author = ctx.author
        guild = ctx.guild
        muted = guild.get_role(self.muted_role)
        await user.remove_roles(muted)

        if await self.is_muted(user):
            _roles = await self.get_muted_roles(user) # Get role IDs from muted user
            roles = [guild.get_role(r[0]) for r in _roles]

            await self.remove_muted(user)
            await user.add_roles(*roles)

            await ctx.send("Unmuted that user.")

            try:
                await user.send(f"You were unmuted in **`{guild}`**.")
            except discord.Forbidden:
                pass

            logged_entry = f"`{author}` ({author.mention}) unmuted `{user}` ({user.mention})\n`reason:` {reason}"
            await self.log_entry(
                ctx,
                text=logged_entry,
                entry_type=Unmute,
                user=user
            )
        else:
            await ctx.send(f"{author.mention}, that user was not muted!")

    @commands.command(description='Unkennels a user and return all of their roles.')
    @is_user()
    async def unkennel(self, ctx, user: discord.Member, *, reason='No reason given.'):
        """ Adds all roles back to user and unmutes them. """
        author = ctx.author
        guild = ctx.guild
        kenneled = guild.get_role(self.kenneled_role)
        await user.remove_roles(kenneled)

        if await self.is_kenneled(user):
            _roles = await self.get_kenneled_roles(user) # Get role IDs from muted user
            roles = [guild.get_role(r[0]) for r in _roles]

            await self.remove_kenneled(user)
            await user.add_roles(*roles)

            await ctx.send("Unkenneled that user.")

            try:
                await user.send(f"You were unkenneled in **`{guild}`**.")
            except discord.Forbidden:
                pass

            logged_entry = f"`{author}` ({author.mention}) unkenneled `{user}` ({user.mention})\n`reason:` {reason}"
            await self.log_entry(
                ctx,
                text=logged_entry,
                entry_type=Unkennel,
                user=user
            )
        else:
            await ctx.send(f"{author.mention}, that user was not kenneled!")

    @commands.group(description='Handles all warn-related information.')
    @is_user()
    async def warn(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send_help("warn")

    @warn.command(description='Warn a user.')
    async def add(self, ctx, user: discord.Member, *, reason='No reason given.'):
        author = ctx.author
        guild = ctx.guild
        identifier = await self.generate_id()
        await self.log_warn(identifier, user, author, reason)
        await ctx.send(
            f"User {user.mention} was warned for {reason} and with a log ID of `{identifier}`."
        )

        try:
            await user.send(
                f"You were warned in **`{guild}`** for **`{reason}`**"
            )
        except discord.Forbidden:
            pass

        await self.log_entry(
            ctx,
            text=f"{author.mention} Warned {user.mention} for "
            f"{reason} and with a log ID of `{identifier}`",
            entry_type=Warn,
            user=user
        )

    @warn.command(aliases=['fetch', 'grab', 'list'], description='Get a warn via specified ID.')
    async def get(self, ctx, identifier):
        ret = await self.fetch_warn(identifier)
        if ret:
            user_id, author_id, reason, date = ret
            user = await self.bot.fetch_user(int(user_id))
            author = await self.bot.fetch_user(int(author_id))
            embed = discord.Embed(
                title=f"Warn retrieved with ID of {identifier}:",
                timestamp=self.strptime(date),
                color=discord.Color(0xe62169)
            )
            embed.add_field(
                name='User:',
                value=f"{user.id} ({user.mention})",
                inline=False
            )
            embed.add_field(
                name='Reason:',
                value=reason,
                inline=False
            )
            embed.add_field(
                name='Issuer:',
                value=f"{author.id} ({author.mention})",
                inline=False
            )
            embed.set_footer(
                text="Warn issued on ->"
            )
            await ctx.send(embed=embed)
        else:
            await ctx.send(f"No warn found with ID {identifier}.")

    @warn.command(aliases=['del', 'rem'], description='Delete a warn via specified ID.')
    async def remove(self, ctx, identifier):
        ret = await self.delete_warn(identifier)
        if ret:
            await ctx.send(f"Deleted the warn with ID {identifier}.")
        else:
            await ctx.send(f"No warn found with ID {identifier}.")

    @warn.command(aliases=['change', 'cng'], description='Edit a warn reason using specified ID.')
    async def edit(self, ctx, identifier, *, reason):
        ret = await self.change_warn(identifier, reason)
        if ret:
            await ctx.send(f"Edited warn `#{identifier}` to `{reason}`.")
        else:
            await ctx.send(f"No warn found with ID {identifier}.")

    @warn.command(aliases=['fetchall', 'graball', 'listall'], description='List all warns of a user.')
    async def getall(self, ctx, user: discord.Member):
        warns = await self.fetch_user_warns(user)
        embed = discord.Embed(
            title=f'Fetching warns for `{user}`...',
            description=f"{len(warns)} warns in total for this user.",
            timestamp=datetime.datetime.utcnow(),
            color=discord.Color(0xe62169)
        )
        for entry, warn in enumerate(warns):
            warn_id, warn_author, warn_reason, warn_ts = warn
            ts = self.strptime(warn_ts)
            formatted = ts.strftime("%b %d, %Y at %I:%M:%S %p (UTC-0)")
            author = self.bot.get_user(int(warn_author))
            if author is None:
                author = await self.bot.fetch_user(int(warn_author))
            embed.add_field(
                name=f'Entry #{entry + 1}:',
                value=f"**`ID:`** #{warn_id}\n" \
                    f"**`Issuer:`** {author.id} ({author.mention})\n" \
                    f"**`Reason:`** {warn_reason}\n" \
                    f"**`Occured on:`** {formatted}",
                inline=False
            )
            total = math.ceil(len(embed.fields) / self.pagination_amt)
            embed.set_footer(text=f"Page 1 of {total}")
        if len(embed.fields) > 0:
            _embed = embed.copy()
            _embed._fields = _embed._fields[:self.pagination_amt]
            msg = await ctx.send(embed=_embed)
            await self.paginate(msg, author, embed)
        else:
            await ctx.send(f"No warns were found for {user.mention}.")


def setup(bot):
    bot.add_cog(Moderator(bot))

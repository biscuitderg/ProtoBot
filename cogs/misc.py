import discord
from discord.ext import commands
from cogs.mod import is_user

import datetime
import sys


class Misc(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot_version = '2.4.3'

    @commands.command(description='Check current ping.')
    @is_user()
    async def ping(self, ctx):
        """ Return client connection latency. """
        latency = self.bot.latency
        embed = discord.Embed(
            title='Ping!',
            description='{}ms'.format(round(latency * 1000)),
            timestamp=datetime.datetime.utcnow(),
            color=discord.Color(0xe62169)
        )

    @commands.command(description='Check bot version.')
    @is_user()
    async def version(self, ctx):
        """Prints current bot version"""
        await ctx.send(
            f'I am currently running on ProtoBot version {self.bot_version} with '
            'python version {}.{}!'.format(*tuple(sys.version_info)[:2])
        )
'''
    @commands.command(pass_context=True)
    @is_user()
    async def help(self, ctx):
        """Prints help message"""
        highest_role = get_highest_role(ctx.author)
        to_send = help_message(highest_role, bot.command_prefix)
        print(to_send)
        if to_send:
            await ctx.channel.send(to_send)
'''


def setup(bot):
    bot.add_cog(Misc(bot))
import datetime

import discord
from discord.ext import commands

from cogs.mod import is_user


class Misc(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot_version = '3.0.0'

    @commands.command(description="Check client websocket connection latency.")
    @is_user()
    async def ping(self, ctx):
        """ Check client websocket connection latency. """
        latency = self.bot.latency
        embed = discord.Embed(
            title='Ping!',
            description='{}ms'.format(round(latency * 1000)),
            timestamp=datetime.datetime.utcnow(),
            color=discord.Color(0xe62169)
        )
        await ctx.send(embed=embed)

    @commands.command(description="Check current bot version.")
    @is_user()
    async def version(self, ctx):
        """ Check current bot version. """
        await ctx.send(
            f'I am currently running on ProtoBot version {self.bot_version}'
        )  # *tuple(sys.version_info)[:2]


def setup(bot):
    bot.add_cog(Misc(bot))

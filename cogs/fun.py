import json
import random

from discord.ext import commands

from cogs.utils.modUtils import ModUtils


class FunMsgs:
    def __init__(self):
        with open("./jsons/fun_msgs.json", encoding='utf-8') as f:
            msgs = json.load(f)
        self.msgs = msgs

    def get(self, param):
        return self.msgs[param]


class Fun(commands.Cog):
    def __init__(self, bot):
        self.fun_msgs = FunMsgs()
        self.bot = bot
        self.owo_msg = self.fun_msgs.get("owo_msg")
        self.nut = self.fun_msgs.get("nut")
        self.seals = self.fun_msgs.get("seals")
        self.quote_channel = ModUtils.get_channel('quote_channel')

    @commands.command(description="What's this?")
    async def owo(self, ctx):
        """ What's this? """
        author = ctx.author
        await ctx.send(f"{author.mention},\n{self.owo_msg}")

    @commands.command(description="█▀█ █▄█ ▀█▀")
    async def bignut(self, ctx):
        """ █▀█ █▄█ ▀█▀ """
        await ctx.send(self.nut)

    @commands.command(description="Prints random navy seal copypasta!")
    async def seal(self, ctx):
        """ Prints random navy seal copypasta! """
        await ctx.send(random.choice(self.seals))


def setup(bot):
    bot.add_cog(Fun(bot))

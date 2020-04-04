import asyncio

import markovify as markov  # we would be overriding this with our class if I didn't do this
from discord.ext import commands

from cogs.utils.modUtils import ModUtils


class Markovify(commands.Cog, ModUtils):
    def __init__(self, bot):
        super().__init__(bot)
        self.bot = bot
        self.msg_channel = self.get_channel('markovify_channel')
        self.msgs = None
        self.text_model = None
        self.cooldown = 1800

    @commands.Cog.listener()
    async def on_ready(self):
        with open('./messages.txt', encoding='utf-8') as f:
            self.msgs = f.read()
        self.text_model = markov.NewlineText(self.msgs)

        while True:
            msg = self.text_model.make_sentence()
            channel = self.bot.get_channel(self.msg_channel)
            await channel.send(msg)
            await asyncio.sleep(self.cooldown)

    @commands.command(description="Change cooldown of the markovify messages.")
    async def change_cooldown(self, ctx, cooldown: int):
        """ Change cooldown of the markovify messages. """
        self.cooldown = cooldown
        await ctx.send("The cooldown has been changed to {}.".format(cooldown))


def setup(bot):
    bot.add_cog(Markovify(bot))

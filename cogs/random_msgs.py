import asyncio

import markovify as markov  # we would be overriding this with our class if I didn't do this
from discord.ext import commands, tasks

from cogs.utils.modUtils import ModUtils


class Markovify(commands.Cog, ModUtils):
    def __init__(self, bot):
        super().__init__(bot)
        self.bot = bot
        self.msg_channel = self.get_channel('markovify_channel')
        with open('./messages.txt', encoding='utf-8') as f:
            self.msgs = f.read()
        self.text_model = markov.NewlineText(self.msgs)
        self.generate_messages.start()
        

    @tasks.loop(seconds=1800.0)
    async def generate_messages(self):
        msg = self.text_model.make_sentence()
        channel = self.bot.get_channel(self.msg_channel)
        await channel.send(msg)
        
    @generate_messages.before_loop
    async def before_messages(self):
        await self.bot.wait_until_ready()

    @commands.command(description="Change cooldown of the markovify messages.")
    async def change_cooldown(self, ctx, cooldown: int):
        """ Change cooldown of the markovify messages. """
        self.generate_messages.change_interval(seconds=cooldown)
        await ctx.send("The cooldown has been changed to {}.".format(cooldown))


def setup(bot):
    bot.add_cog(Markovify(bot))

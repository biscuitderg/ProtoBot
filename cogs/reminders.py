import datetime
import re

import discord
from discord.ext import commands, tasks

from cogs.utils.database import Database
from cogs.utils.modUtils import ModUtils


class Reminders(commands.Cog, ModUtils):
    def __init__(self, bot):
        super().__init__(bot)
        self.bot = bot
        self.db = Database('./dbs/reminders.db')
        self.check_reminders.start()

    @staticmethod
    def get_unit(param):
        params = {
            "w": "weeks",
            "d": "days",
            "h": "hours",
            "m": "minutes",
            "s": "seconds"
        }
        return params[param]

    @commands.Cog.listener()
    async def on_ready(self):
        await self.db.ensure(
            """
            CREATE TABLE IF NOT EXISTS reminders
            (author string,
            channel string,
            delta timestamp,
            message string,
            UNIQUE(author, channel, delta, message))
            """
        )

    @tasks.loop(seconds=5.0)
    async def check_reminders(self):
        for r in await self.db.execute("SELECT * FROM reminders"):
            author, channel, delta, message = r
            if self.strptime(delta) <= self.now:
                await self._remind(int(author), int(channel), message)

    @check_reminders.before_loop
    async def before_check(self):
        await self.bot.wait_until_ready()

    async def _remind(self, author_id, channel_id, message):
        author = await self.get_user(author_id)
        channel = self.bot.get_channel(channel_id)
        if channel is None:
            channel = await self.bot.fetch_channel(channel_id)

        embed = discord.Embed(
            title="New Reminder!",
            description=f"{author.mention}, you have a new reminder:",
            timestamp=self.now,
            color=discord.Color(0xe62169)
        )
        embed.add_field(
            name="Reminder:",
            value=f'"{message}"'
        )
        await channel.send(content=author.mention, embed=embed)
        await self.del_reminder(author, message)

    async def del_reminder(self, author, message):
        """
        Removes a reminder from the database.

        Parameters
        -----------
        author: :class:`discord.Member`
            The author of the reminder.
        message: :class:`str`
            The message of the reminder.
        """

        await self.db.execute(
            "DELETE FROM reminders WHERE author=? AND message=?",
            (author.id, message)
        )

    async def add_reminder(self, author, channel, delta, message):
        """
        Adds a reminder to the database.

        Parameters
        -----------
        author: :class:`discord.Member`
            The author of the reminder.
        channel: :class:`discord.Channel`
            The channel of the reminder.
        delta: :class:`datetime.datetime`
            The date to initiate the reminder.
        message: :class:`str`
            The message of the reminder.
        """

        await self.db.execute(
            "INSERT INTO reminders (author, channel, delta, message) "
            "VALUES(?, ?, ?, ?)",
            (author.id, channel.id, delta, message)
        )

    @commands.command(aliases=['add_reminder', 'remind_me', 'reminder'], description="Set up a new reminder for yourself.")
    async def remind(self, ctx, *, message):
        """ Set up a new reminder for yourself. """
        v_pattern = re.compile(r'(in.?)(\d+)')
        value = [v.group(2) for v in v_pattern.finditer(message)][0]
        u_pattern = re.compile(r'([A-Za-z])([A-Za-z])*$')
        unit_initial = [v.group(1) for v in u_pattern.finditer(message)][0]
        unit = self.get_unit(unit_initial)
        dt_td = datetime.timedelta(**{unit: int(value)})
        delta = self.now + dt_td

        message = message \
            .replace([v.group(0) for v in v_pattern.finditer(message)][0], "") \
            .replace(unit_initial, "") \
            .strip()
        await self.add_reminder(
            ctx.author,
            ctx.channel,
            delta.replace(microsecond=0),
            message
        )
        await ctx.send(
            "Reminder set. I will remind you in {} {} about {}.".format(value, unit, message)
        )


def setup(bot):
    bot.add_cog(Reminders(bot))

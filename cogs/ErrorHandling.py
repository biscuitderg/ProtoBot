import math
import sys
import traceback

import discord
from discord.ext import commands
from discord.ext.commands.errors import *

from cogs import mod


class ErrorHandling(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        cmd = ctx.command
        if hasattr(cmd, 'on_error'):
            return
        error = getattr(error, 'original', error)

        if isinstance(error, CommandNotFound):
            return
        elif isinstance(error, mod.MissingPermissions) or isinstance(error, mod.NoAccess):
            await ctx.send(f"Error in command: `{cmd}`:\n```{error}```")
        elif isinstance(error, CheckFailure):
            if isinstance(error, NSFWChannelRequired):
                await ctx.send(f'Error in command `{cmd}`:\n```{error}```')
                if not isinstance(ctx.channel, discord.DMChannel):
                    await ctx.message.delete()
            elif isinstance(error, PrivateMessageOnly) or isinstance(error, NoPrivateMessage) or isinstance(error,
                                                                                                            commands.BotMissingPermissions):
                await ctx.send(f'Error in command `{cmd}`:\n```{error}```')
            else:
                return
        elif isinstance(error, CommandOnCooldown):
            cooldown = cooldown_formatter(error.retry_after)
            await ctx.send(f"You must wait {cooldown} before you can use the command ``{cmd}`` again.")
        elif isinstance(error, commands.UserInputError):
            if isinstance(error, commands.MissingRequiredArgument):
                await ctx.send_help(cmd)
            else:
                await ctx.send(f'Error in command `{cmd}`:\n```{type(error).__name__}: {error}```')
        else:
            print(f'>>> Occurred in {ctx.guild}, in {ctx.channel} by user {ctx.author}')
            await ctx.send(f'Error in command `{cmd}`:\n```{type(error).__name__}: {error}```')
            print('Ignoring exception in command {}:'.format(cmd), file=sys.stderr)
            traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)


# Cooldown formatter
def cooldown_formatter(cooldown):
    cooldown = round(cooldown)
    days = math.floor(cooldown / 86400)
    hours = math.floor(cooldown / 3600) - (days * 24)
    minutes = math.floor(cooldown / 60) - (hours * 60) - (days * 24 * 60)
    seconds = cooldown - (minutes * 60) - (hours * 3600) - (days * 86400)
    dt = date_string(days, 'day')
    ht = date_string(hours, 'hour')
    mt = date_string(minutes, 'minute')
    st = date_string(seconds, 'second')

    times_before = [dt, ht, mt, st]
    times_after = []

    for time_unit in times_before:
        if time_unit == '':
            continue
        else:
            times_after.append(time_unit)

    if len(times_after) == 1:
        return times_after[0]
    else:
        beginning = ' '.join(times_after[:-1])
        end = f'and {times_after[-1]}'

        return f'{beginning} {end}'


# Date string
def date_string(time, unit):
    time = int(time)
    if time == 1:
        if unit == 'second':
            return f'1 {unit}'
        else:
            return f'1 {unit},'
    elif time == 0:
        return ''
    else:
        if unit == 'second':
            return f'{time} {unit}s'
        return f'{time} {unit}s,'


def setup(bot):
    bot.add_cog(ErrorHandling(bot))
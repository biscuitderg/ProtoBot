import os
from copypastas import *
import discord
import asyncio
from dotenv import load_dotenv
from discord.ext import commands
from aiofile import AIOFile, LineReader, Writer
import datetime

load_dotenv()
token = os.getenv('DISCORD_TOKEN')


# Create custom bot class
class CustomBot(commands.Bot):
    async def on_ready(self):
        print(f'{self.user} has connected to Discord!')
        await self.change_presence(activity=discord.Game(name=self.command_prefix + 'help | v' + version))

        while True:
            await asyncio.sleep(60)
            await check_reminders()

    async def on_message(self, message):
        highest_role = get_highest_role(message.author)

        if message.content.lower() == 'protobot reset prefix':
            if check_permission(highest_role, role_dict, 'updateprefix'):
                self.command_prefix = '$'
                await message.channel.send('Prefix reset to `' + self.command_prefix + '`')
                await self.change_presence(activity=discord.Game(name=self.command_prefix + 'help | v' + version))
            else:
                await message.channel.send('I uh, can\'t do that for you! ᶦ\'ᵐ ˢᵒʳʳʸ')

        if message.content.lower().startswith('>pfpwarn') and message.channel.id == 575101474032582676 and highest_role != 'recruit':
            try:
                user_to_mention = message.content.split(' ')[1]
            except IndexError:
                pass
            else:
                if user_to_mention[0] != '<':
                    user_to_mention = '<@' + str(user_to_mention) + '>'
                init_message = 'Sending a reminder for checking on ' + user_to_mention + ' in 24 hours!'
                await message.channel.send(init_message)
                to_send = 'Check on ' + str(user_to_mention) + '\'s profile picture!'
                await add_reminder(message, duration=86400, reminder_text=to_send)
        # If you don't call this coroutine you can't process commands
        await self.process_commands(message)


# Call custom bot class
bot = CustomBot(command_prefix='$')
bot.remove_command('help')
version = '1.0.0'


# Define helper commands/functions
async def add_reminder(message, duration, reminder_text=''):
    async with AIOFile('reminders.txt', 'a+', encoding='utf-8') as reminders:
        writer = Writer(reminders)
        caller_id = message.author.id
        channel_id = message.channel.id
        duration_delta = datetime.timedelta(seconds=duration)
        reminder_date = datetime.datetime.utcnow() + duration_delta
        await writer(reminder_date.isoformat() + ' ' + str(channel_id) + ' ' + str(caller_id) + ' ' + reminder_text + '\n')


def get_highest_role(author):
    user_roles = [r.name.lower() for r in author.roles if r.name.lower() in role_list]
    if user_roles:
        return user_roles[-1]
    else:
        return


async def check_reminders():
    with open('reminders.txt', 'r+', encoding='utf-8') as reminders:
        lines = reminders.readlines()
    async with AIOFile('reminders.txt', 'w+', encoding='utf-8') as reminders:
        writer = Writer(reminders)
        for line in lines:
            items = line.strip('\n').split(' ')
            reminder_date = datetime.datetime.fromisoformat(items[0])
            channel = bot.get_channel(int(items[1]))
            caller = items[2]
            to_send = ''
            if len(items) > 3:
                to_send = '<@' + caller + '>: ' + ' '.join(items[3:])
            if reminder_date < datetime.datetime.utcnow():
                if to_send:
                    await channel.send(to_send)
            else:
                await writer(line)


# Creating command groups
# Misc category
class Misc(commands.Cog, name='Misc.'):
    """Miscellaneous/testing commands!"""
    @bot.command(pass_context=True)
    async def ping(self, ctx):
        """Pong!"""
        await ctx.channel.send('Pong!')

    @bot.command(pass_context=True)
    async def version(self, ctx):
        """Prints current bot version"""
        await ctx.channel.send(version)

    @bot.command(pass_context=True)
    async def help(self, ctx):
        """Prints help message"""
        highest_role = get_highest_role(ctx.author)
        to_send = help_message(highest_role, bot.command_prefix)
        await ctx.channel.send(to_send)


# Fun category
class Fun(commands.Cog, name='Fun'):
    """Fun commands to play around with!"""
    @bot.command(pass_context=True)
    async def owo(self, ctx):
        """What's this?"""
        await ctx.channel.send(owo)

    @bot.command(pass_context=True)
    async def bignut(self, ctx):
        """█▀█ █▄█ ▀█▀"""
        await ctx.channel.send("""█▀█ █▄█ ▀█▀""")


# Moderation category
class Moderation(commands.Cog, name='Moderation'):
    """Tools for moderators to use!"""
    @bot.command(pass_context=True)
    async def reminder(self, ctx, duration: int, *args):
        """Sends a reminder after the given amount of time"""
        highest_role = get_highest_role(ctx.author)
        if check_permission(highest_role, role_dict, 'reminder'):
            await asyncio.sleep(1)
            init_message = 'Sending a reminder in ' + str(duration) + ' seconds!'
            if args:
                reminder_text = ' '.join(args)
            else:
                reminder_text = ''
            await add_reminder(ctx, duration, reminder_text=reminder_text)
            await ctx.channel.send(init_message)
        else:
            await ctx.channel.send('I uh, can\'t do that for you! ᶦ\'ᵐ ˢᵒʳʳʸ')


# Admin category
class Admin(commands.Cog, name='Administrative'):
    """Tools for admins to use!"""
    @bot.command(pass_context=True)
    async def updateprefix(self, ctx, prefix: str):
        highest_role = get_highest_role(ctx.author)
        if check_permission(highest_role, role_dict, 'updateprefix'):
            if not prefix:
                await ctx.channel.send('That\'s not a valid prefix TwT')
            else:
                if len(prefix) > 3:
                    await ctx.channel.send('>///< your prefix is too big~')
                else:
                    bot.command_prefix = prefix
                    await ctx.channel.send('Prefix changed to `' + prefix + '` succesfully!')
                    await bot.change_presence(activity=discord.Game(name=prefix + 'help | v' + version))


bot.recursively_remove_all_commands()
cogs = [Fun(), Moderation(), Misc(), Admin()]
for cog in cogs:
    bot.add_cog(cog)
bot.run(token)

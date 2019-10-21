import os
from copypastas import *
import discord
import asyncio
from dotenv import load_dotenv
from discord.ext import commands
from aiofile import AIOFile, LineReader, Writer
import datetime
import re
import pickle

load_dotenv()
token = os.getenv('DISCORD_TOKEN')
scrape_channel = None
log_channel = None
internal_cache = {}


# Create custom bot class
class CustomBot(commands.Bot):

    async def on_ready(self):
        print(f'{self.user} has connected to Discord!')
        await self.change_presence(activity=discord.Game(name=self.command_prefix + 'help | v' + version))

        while True:
            await asyncio.sleep(60)
            await check_reminders()

    async def log_entry(self, embed_text):
        """Will add entry to protobot logs"""
        pass

    """async def cache_message(self, message, message_type):
        message_id = message.id
        author = message.author.name
        author_id = message.author.id
        channel_id = message.channel.id
        if message.embeds:
            pass"""

    async def process_commands(self, message):
        if message.author.bot:
            return

        ctx = await self.get_context(message)
        await self.invoke(ctx)

    async def on_message(self, message):
        highest_role = get_highest_role(message.author)

        if message.content.lower() == 'protobot reset prefix':
            if check_permission(highest_role, role_dict, 'updateprefix'):
                self.command_prefix = '$'
                await message.channel.send('Prefix reset to `' + self.command_prefix + '`')
                await self.change_presence(activity=discord.Game(name=self.command_prefix + 'help | v' + version))
            else:
                await message.channel.send('I uh, can\'t do that for you! ᶦ\'ᵐ ˢᵒʳʳʸ')

        if (message.content.lower().startswith('>pfpwarn') or message.content.lower().startswith('>hitlerwarn')) \
                and message.channel.id == 575101474032582676 and highest_role != 'recruit':
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

    """async def on_raw_message_delete(self, payload):
        if payload.cached_message:
            # add to deleted messages backup cache
            print(payload.cached_message.content)
            if payload.cached_message.embeds:
                for embed in payload.cached_message.embeds:
                    print(embed.to_dict())
            if payload.cached_message.attachments:
                for attachment in payload.cached_message.attachments:
                    print(attachment.url)
        else:
            print(payload)"""

    """async def on_raw_message_edit(self, payload):
        if payload.cached_message:
            # cached message content is original message
            print('before:', payload.message_id, payload.cached_message.content)
            history = await payload.cached_message.channel.history().flatten()
            msg = discord.utils.get(history, id=payload.message_id)
            print('after:', msg.content)"""


# Call custom bot class
bot = CustomBot(command_prefix='$', max_messages=20000)
bot.remove_command('help')
version = '1.1.0'


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
        await ctx.channel.send('I am currently running on version ' + version + '!')

    @bot.command(pass_context=True)
    async def help(self, ctx):
        """Prints help message"""
        highest_role = get_highest_role(ctx.author)
        to_send = help_message(highest_role, bot.command_prefix)
        if to_send:
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
        """Update command prefix"""
        highest_role = get_highest_role(ctx.author)
        if check_permission(highest_role, role_dict, 'updateprefix'):
            if not prefix:
                await ctx.channel.send('That\'s not a valid prefix TwT')
            else:
                if len(prefix) > 3:
                    await ctx.channel.send('>///< your prefix is too big~')
                else:
                    bot.command_prefix = prefix
                    await ctx.channel.send('Prefix changed to `' + prefix + '` successfully!')
                    await bot.change_presence(activity=discord.Game(name=prefix + 'help | v' + version))

    @bot.command(pass_context=True)
    async def log(self, ctx, channel_name: str, *args):
        highest_role = get_highest_role(ctx.author)
        if check_permission(highest_role, role_dict, 'log'):
            print('LOGGING')
            await ctx.channel.send('LOGGING')
            """Create log warning CSVs"""
            # channel IDs
            channels = {
                559221602462597141: 'warnings',
                608385252699930644: 'informals',
                512417242684719136: 'bans',
                586044083764461578: 'unbans'
                }
            # parse month if passed as an argument
            need_month = True
            if args:
                if args[0].isnumeric():
                    month = int(args[0])
                    if 0 < month < 13:
                        need_month = False
            # use regex to pull all strings containing decimal digits
            p = re.compile('\d+')
            # Pull channel string passed as first argument

            if channel_name:
                if channel_name.isnumeric():
                    channel_id = int(channel_name)
                    channel_name = channels[channel_id]
                else:
                    inverted_dict = dict([[v, k] for k, v in channels.items()])
                    try:
                        channel_id = inverted_dict[channel_name]
                    except KeyError:
                        channel_id = int(p.findall(channel_name)[0])
                        channel_name = channels[channel_id]
                channel_to_log = bot.get_channel(channel_id)
                if channel_to_log:
                    lines = ['logger,timestamp,year,month,day,hour,minute,ids_present,message,attachments\n']
                    messages = await channel_to_log.history(limit=2400).flatten()
                    year = messages[0].created_at.year
                    if need_month:
                        month = messages[0].created_at.month
                        month = (month - 1) % 12
                        if month == 0:
                            month = 12
                            year -= 1
                    in_month = [m for m in messages if m.created_at.month == month and m.created_at.year == year]
                    for m in in_month:
                        logger = str(m.author.id)
                        timestamp = [m.created_at.year, m.created_at.month, m.created_at.day,
                                      m.created_at.hour, m.created_at.minute]
                        timestamp = [str(n) for n in timestamp]
                        compact_timestamp = '.'.join([str(n) for n in timestamp])
                        content = ' '.join(m.content.replace(',', '').splitlines())
                        p = re.compile('[@ ]\d+')
                        ids_present = '; '.join(list(set([s[1:] for s in p.findall(content) if len(s) == 19])))
                        if m.attachments:
                            attachments = '; '.join([a.url for a in m.attachments])
                        else:
                            attachments = 'None'
                        lines.append(','.join([logger, compact_timestamp] + timestamp + [ids_present, content, attachments]) + '\n')
                    filename = './logs/' + channel_name + '-' + str(month) + '-' + str(year) + '.csv'
                    with open(filename, 'w+') as logfile:
                        logfile.writelines(lines)

            print("LOG COMPLETE")
            await ctx.channel.send('Here is the requested log file:', file=discord.File(filename))
            pass


class Testing(commands.Cog, name=''):
    """Commands being tested go here!"""
    @bot.command(pass_context=True)
    async def pickletest(self, ctx):
        with open('testpickle', 'w+') as jar:
            message = await ctx.channel.history(limit=1).flatten()
            pickle.dump(message, jar)

    @bot.command(pass_context=True)
    async def channelscrape(self, ctx, channel, *args):
        """Scrape channel for messages!"""
        # parse arguments
        channel_id = int(channel.strip('<#>'))
        found = False
        for channel in bot.get_all_channels():
            if channel_id == channel.id:
                channel_to_scrape = channel
                found = True
        if found:
            messages = await channel_to_scrape.history(limit=10).flatten()
            for message in messages:
                print(message.author, message.author.id, message.content)
        else:
            await ctx.channel.send('Channel not found!')
    pass

bot.recursively_remove_all_commands()
cogs = [Fun(), Moderation(), Misc(), Admin()]
for cog in cogs:
    bot.add_cog(cog)
bot.run(token)
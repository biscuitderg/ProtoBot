import os
from copypastas import *
from seals import *
import discord
import asyncio
from dotenv import load_dotenv
from discord.ext import commands
from aiofile import AIOFile, LineReader, Writer
import datetime
import re
import pickle
import random
import math
import pytz

load_dotenv()
token = os.getenv('DISCORD_TOKEN')
scrape_channel = None
log_channel_id = 641066795909775392
self_id = 632658384767811604
server_id = 241029406796152834
kenneled_role_id = 533806085010620426
kennel_id = 533805835424497666
mute_role_id = 520032107578523678
joins_id = 590990121206153267
internal_cache = {}
eastern = pytz.timezone('US/Eastern')

# Create custom bot class
class CustomBot(commands.Bot):

    async def on_ready(self):
        print(f'{self.user} has connected to Discord!')
        await self.change_presence(activity=discord.Game(name=self.command_prefix + 'help | v' + version))

        self.server = await self.fetch_guild(server_id)
        self.log_channel = self.get_channel(log_channel_id)
        self.join_channel = self.get_channel(joins_id)
        self.kennel_role = self.server.get_role(kenneled_role_id)
        self.muted_role = self.server.get_role(mute_role_id)
        self.me = await self.server.fetch_member(self_id)

        while True:
            await asyncio.sleep(60)
            await check_reminders()

    async def log_entry(self, embed_text, title='', joinleave=False, color=None, member=None):
        """Add entry to protobot logs"""
        if not color:
            color = self.me.color
        embed = discord.Embed(title=title, timestamp=datetime.datetime.utcnow(), color=color, description=embed_text)
        if joinleave:
            if member:
                embed.set_thumbnail(url=member.avatar_url)
                footertext = 'ID: ' + str(member.id)
            embed.set_footer(text=footertext)
            await self.join_channel.send(embed=embed)
            pass
        else:
            await self.log_channel.send(embed=embed)
        pass

    async def process_commands(self, message):
        if message.author.bot:
            return

        ctx = await self.get_context(message)
        # Permission check!
        highest_role = get_highest_role(ctx.author)
        try:
            if check_permission(highest_role, role_dict, ctx.command):
                await self.invoke(ctx)
            else:
                if highest_role in role_list:
                    await ctx.channel.send('Sowwy, wooks wike u cant use that command, oopsie!')
                else:
                    pass
        except KeyError:
            pass

    async def on_message(self, message):
        if message.author.bot:
            pass
        try:
            highest_role = get_highest_role(message.author)
        except AttributeError:
            highest_role = None

        if message.content.lower() == 'protobot reset prefix':
            if check_permission(highest_role, role_dict, 'updateprefix'):
                self.command_prefix = '$'
                await message.channel.send('Prefix reset to `' + self.command_prefix + '`')
                await self.change_presence(activity=discord.Game(name=self.command_prefix + 'help | v' + version))
                embed_text = '<@' + str(message.author.id) + '> ' + message.author.name + '#' + message.author.discriminator + \
                             ' reset prefix to `' + self.command_prefix + '`'
                await bot.log_entry(embed_text, title='Command used')
            else:
                await message.channel.send('I uh, can\'t do that for you! ᶦ\'ᵐ ˢᵒʳʳʸ')

        # If you don't call this coroutine you can't process commands
        await self.process_commands(message)

    async def on_member_join(self, member):
        embed_text = '<@' + str(member.id) + '> ' + member.name + '#' + member.discriminator
        now = datetime.datetime.utcnow()
        delta = now - member.created_at
        s = delta.total_seconds()
        if s < 5*86400:
            embed_text += '\n' + duration_text(s)
        await self.log_entry(embed_text, title='User Joined', joinleave=True, color=discord.Colour.green(), member=member)

    async def on_member_remove(self, member):
        embed_text = '<@' + str(member.id) + '> ' + member.name + '#' + member.discriminator
        await self.log_entry(embed_text, title='User Left', joinleave=True, color=discord.Colour.red(), member=member)


# Call custom bot class
bot = CustomBot(command_prefix='$', max_messages=20000)
bot.remove_command('help')
version = '2.1.1'


# Define helper commands/functions
async def add_reminder(message, duration, reminder_text=''):
    async with AIOFile('reminders.txt', 'a+', encoding='utf-8') as reminders:
        writer = Writer(reminders)
        caller_id = message.author.id
        channel_id = message.channel.id
        duration_delta = datetime.timedelta(seconds=duration)
        reminder_date = datetime.datetime.utcnow() + duration_delta
        await writer(reminder_date.isoformat() + ' ' + str(channel_id) + ' ' +
                     str(caller_id) + ' ' + reminder_text + '\n')


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

    @bot.command(pass_context=True)
    async def seal(self, ctx):
        """Prints random navy seal copypasta!"""
        to_send = random.choice(seals)
        await ctx.channel.send(to_send)


# Moderation category
class Moderation(commands.Cog, name='Moderation'):
    """Tools for moderators to use!"""
    @bot.command(pass_context=True)
    async def reminder(self, ctx, duration: int, *args):
        """Sends a reminder after the given amount of time"""
        await asyncio.sleep(1)
        init_message = 'Sending a reminder in ' + str(duration) + ' seconds!'
        if args:
            reminder_text = ' '.join(args)
        else:
            reminder_text = ''
        await add_reminder(ctx, duration, reminder_text=reminder_text)
        await ctx.channel.send(init_message)

    @bot.command(pass_context=True)
    async def kennel(self, ctx, user, *args):
        """Removes all roles from user and adds kennel role!"""
        reason = ' '.join(args)
        # get user, current roles
        p = re.compile('\d+')
        user_id = int(p.findall(user)[0])
        user_to_change = await bot.server.fetch_member(user_id)
        user_roles = [r for r in user_to_change.roles if r < bot.me.top_role and r.name.lower() != 'nitro booster']
        msg = ''
        if len(user_roles) > 1:
            await user_to_change.remove_roles(*user_roles[1:], reason=reason)
            msg += ', '.join([r.name.lower() for r in user_roles[1:]]) + ', kenneled'
        await user_to_change.add_roles(bot.kennel_role, reason=reason)
        try:
            if user_to_change.dm_channel:
                await user_to_change.dm_channel.send('You have a message waiting in <#' + str(kennel_id) + '> on the /r/yiff server!')
            else:
                await user_to_change.create_dm()
                await user_to_change.dm_channel.send('You have a message waiting in <#' + str(kennel_id) + '> on the /r/yiff server!')
        except discord.HTTPException or discord.Forbidden:
            await ctx.channel.send('Could not send DM!')
        else:
            await ctx.channel.send('User kenneled and notified!')
        embed_text = '<@' + str(ctx.author.id) + '> ' + ctx.author.name + '#' + ctx.author.discriminator + ' used `$kennel` command on <@' + str(user_id) \
                     + '> ' + user_to_change.name + '#' + user_to_change.discriminator + '\nReason: ' + reason
        await bot.log_entry(embed_text, title='Command used')
        if not msg:
            msg = 'kenneled'
        await ctx.channel.send('Following roles changed for ' + user_to_change.name + '#' + user_to_change.discriminator + ': ' + msg)

    @bot.command(pass_context=True)
    async def mute(self, ctx, user, *args):
        """Removes all roles from user and adds muted role!"""
        reason = ' '.join(args)
        # get user, current roles
        p = re.compile('\d+')
        user_id = int(p.findall(user)[0])
        user_to_change = await bot.server.fetch_member(user_id)
        user_roles = [r for r in user_to_change.roles if r < bot.me.top_role and r.name.lower() != 'nitro booster']
        msg = ''
        if len(user_roles) > 1:
            await user_to_change.remove_roles(*user_roles[1:], reason=reason)
            msg += ', '.join([r.name.lower() for r in user_roles[1:]]) + ', muted'
        await user_to_change.add_roles(bot.muted_role, reason=reason)
        await ctx.channel.send('User muted! Set a reminder to remind you to unmute!')
        embed_text = '<@' + str(
            ctx.author.id) + '> ' + ctx.author.name + '#' + ctx.author.discriminator + ' used `$mute` command on <@' + str(
            user_id) \
                     + '> ' + user_to_change.name + '#' + user_to_change.discriminator + '\nReason: ' + reason
        await bot.log_entry(embed_text, title='Command used')
        if not msg:
            msg = 'muted'
        await ctx.channel.send('Following roles changed for ' + user_to_change.name + '#' + user_to_change.discriminator + ': ' + msg)

    @bot.command(pass_context=True)
    async def role(self, ctx, user, *args):
        """Adds removes or toggles roles for a user"""
        # parse roles to add or remove based on dyno syntax
        roles = ' '.join(args)
        roles = [r.strip() for r in roles.split(',')]
        roles_mentioned = [r[1:].lower() for r in roles if r.startswith('+') or r.startswith('-')]
        roles_mentioned += [r.lower() for r in roles if not (r.startswith('+') or r.startswith('-'))]
        roles_mentioned = list(set(roles_mentioned))
        roles_to_add = [r[1:].lower() for r in roles if r.startswith('+')]
        roles_to_remove = [r[1:].lower() for r in roles if r.startswith('-')]
        roles = [r.lower() for r in roles_mentioned if r.lower() not in roles_to_add or r.lower() not in roles_to_remove]
        # get user, current roles
        p = re.compile('\d+')
        user_id = int(p.findall(user)[0])
        user_to_change = await bot.server.fetch_member(user_id)
        if user_to_change:
            user_has = [r.name.lower() for r in user_to_change.roles]
            roles_to_add += [r for r in roles if r.lower() not in user_has and r.lower() not in roles_to_add]
            roles_to_remove += [r for r in roles if r.lower() in user_has and r.lower() not in roles_to_remove and r.lower() not in roles_to_add]
            roles_to_add = [r for r in roles_to_add if r.lower() not in roles_to_remove]
            failed_roles = []
            msg = 'Made the following changes to ' + user_to_change.name + '#' + user_to_change.discriminator + ': '
            add_roles = []
            remove_roles = []
            for role in roles_to_add:
                role_to_add = discord.utils.find(lambda m: m.name.lower() == role, bot.server.roles)
                if role_to_add and role_to_add < bot.me.top_role:
                    msg += '+' + role_to_add.name + ', '
                    add_roles.append(role_to_add)
                else:
                    failed_roles.append(role)

            for role in roles_to_remove:
                role_to_remove = discord.utils.find(lambda m: m.name.lower() == role, bot.server.roles)
                if role_to_remove and role_to_remove < bot.me.top_role:
                    msg += '-' + role_to_remove.name + ', '
                    remove_roles.append(role_to_remove)
                else:
                    failed_roles.append(role)
            try:
                await user_to_change.add_roles(*add_roles)
                await user_to_change.remove_roles(*remove_roles)
            except discord.Forbidden:
                await ctx.channel.send('I don\'t have the proper permissions!')
            except discord.HTTPException:
                await ctx.channel.send('Failed to change roles!')
            else:
                if not add_roles and not remove_roles:
                    await ctx.channel.send('No changes made!')
                else:
                    if failed_roles:
                        msg = msg[:-2] + '\nFailed to change roles: ' + ', '.join(failed_roles)
                    else:
                        msg = msg[:-2]
                    await ctx.channel.send(msg)
            embed_text = '<@' + str(ctx.author.id) + '> ' + ctx.author.name + '#' + ctx.author.discriminator + \
                         ' used `$role` command on <@' + str(user_id) + '> ' + user_to_change.name + '#' + user_to_change.discriminator
            await bot.log_entry(embed_text, title='Command used')

    @bot.command(pass_context=True)
    async def pfpwarn(self, ctx, user):
        """Warn for NSFW pfp!"""
        # get user
        p = re.compile('\d+')
        user_id = int(p.findall(user)[0])
        user_to_dm = await bot.server.fetch_member(user_id)
        msg = 'We noticed you have a NSFW profile picture. We do not allow this as it violates Discord ToS. If you don\'' \
            + 't change it within 24 hours we will have no choice but to ban you from the server until you have a SFW '\
            + 'icon. Thanks for understanding ^^ - <@' + str(ctx.author.id) + '> at /r/yiff'
        try:
            if user_to_dm.dm_channel:
                await user_to_dm.dm_channel.send(msg)
            else:
                await user_to_dm.create_dm()
                await user_to_dm.dm_channel.send(msg)
        except discord.HTTPException or discord.Forbidden:
            await ctx.channel.send('Could not send DM!')
        else:
            await ctx.channel.send('User notified!')
        embed_text = '<@' + str(
            ctx.author.id) + '> ' + ctx.author.name + '#' + ctx.author.discriminator + ' used `$pfpwarn` command on <@'\
            + str(user_id) + '> ' + user_to_dm.name + '#' + user_to_dm.discriminator
        await bot.log_entry(embed_text, title='Command used')
        await add_reminder(ctx, 24*60*60, 'Check on <@' + str(user_to_dm.id) + '>\'s pfp!')
        await ctx.channel.send('Reminder added!')

    @bot.command(pass_context=True)
    async def hitlerwarn(self, ctx, user):
        """Warn for rulebreaking pfp!"""
        # get user
        p = re.compile('\d+')
        user_id = int(p.findall(user)[0])
        user_to_dm = await bot.server.fetch_member(user_id)
        msg = 'We noticed you have a rulebreaking profile picture. We do not allow this as it violates server rules on allowable. If you don\'' \
              + 't change it within 24 hours we will have no choice but to ban you from the server until you have an acceptable ' \
              + 'icon. Thanks for understanding ^^ - <@' + str(ctx.author.id) + '> at /r/yiff'
        try:
            if user_to_dm.dm_channel:
                await user_to_dm.dm_channel.send(msg)
            else:
                await user_to_dm.create_dm()
                await user_to_dm.dm_channel.send(msg)
        except discord.HTTPException or discord.Forbidden:
            await ctx.channel.send('Could not send DM!')
        else:
            await ctx.channel.send('User notified!')
        embed_text = '<@' + str(
            ctx.author.id) + '> ' + ctx.author.name + '#' + ctx.author.discriminator + ' used `$hitlerwarn` command on <@' \
                     + str(user_id) + '> ' + user_to_dm.name + '#' + user_to_dm.discriminator
        await bot.log_entry(embed_text, title='Command used')
        await add_reminder(ctx, 24 * 60 * 60, 'Check on <@' + str(user_to_dm.id) + '>\'s pfp!')
        await ctx.channel.send('Reminder added!')

# Admin category
class Admin(commands.Cog, name='Administrative'):
    """Tools for admins to use!"""
    @bot.command(pass_context=True)
    async def updateprefix(self, ctx, prefix: str):
        """Update command prefix"""
        if not prefix:
            await ctx.channel.send('That\'s not a valid prefix TwT')
        else:
            if len(prefix) > 3:
                await ctx.channel.send('>///< your prefix is too big~')
            else:
                bot.command_prefix = prefix
                await ctx.channel.send('Prefix changed to `' + prefix + '` successfully!')
                await bot.change_presence(activity=discord.Game(name=prefix + 'help | v' + version))
                embed_text = '<@' + str(ctx.author.id) + '> ' + ctx.author.name + '#' + ctx.author.discriminator + \
                             ' used `$updateprefix` command, changed to `' + prefix + '`'
                await bot.log_entry(embed_text, title='Command used')

    @bot.command(pass_context=True)
    async def log(self, ctx, channel_name: str, *args):
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
                with open(filename, 'w+', encoding='utf-8') as logfile:
                    logfile.writelines(lines)

        print("LOG COMPLETE")
        await ctx.channel.send('Here is the requested log file:', file=discord.File(filename))
        embed_text = '<@' + str(ctx.author.id) + '> ' + ctx.author.name + '#' + ctx.author.discriminator +\
                     'used `$log` command for <#' + str(channel_id) + '>'
        await bot.log_entry(embed_text, title='Command used')
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


"""if (message.content.lower().startswith('>pfpwarn') or message.content.lower().startswith('>hitlerwarn')) \
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
                await add_reminder(message, duration=86400, reminder_text=to_send)"""
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
"""async def cache_message(self, message, message_type):
     message_id = message.id
     author = message.author.name
     author_id = message.author.id
     channel_id = message.channel.id
     if message.embeds:
         pass"""

bot.recursively_remove_all_commands()
cogs = [Fun(), Moderation(), Misc(), Admin()]
for cog in cogs:
    bot.add_cog(cog)
bot.run(token)

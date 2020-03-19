import os
from copypastas import *
from seals import *
import discord
import asyncio
from dotenv import load_dotenv
from discord.ext import commands
from aiofile import AIOFile, Writer
import datetime
import dateparser
import re
import random
import pytz
import sys
import traceback
import markovify

load_dotenv()
token = os.getenv('DISCORD_TOKEN')
scrape_channel = None
log_channel_id = 641066795909775392
error_channel_id = 647470122243588137
self_id = 632658384767811604
server_id = 241029406796152834
kenneled_role_id = 533806085010620426
kennel_id = 533805835424497666
mute_role_id = 520032107578523678
joins_id = 590990121206153267
starboard_channel = 665048291012116480
ban_channel = 512417242684719136
unban_channel = 586044083764461578
carl_id = 633707432144535571
proto_fun_channel = 683130359818616864
internal_cache = {}
eastern = pytz.timezone('US/Eastern')
testmode = False
with open('messages.txt', encoding='utf-8') as f:
    text = f.read()
text_model = markovify.NewlineText(text)

# Create custom bot class
class CustomBot(commands.Bot):

    async def on_command_error(self, context, exception):
        """|coro|

        The default command error handler provided by the bot.

        By default this prints to :data:`sys.stderr` however it could be
        overridden to have a different implementation.

        This only fires if you do not specify any listeners for command error.
        """
        if self.extra_events.get('on_command_error', None):
            return

        if hasattr(context.command, 'on_error'):
            return

        cog = context.cog
        if cog:
            if commands.Cog._get_overridden_method(cog.cog_command_error) is not None:
                return

        print('Ignoring exception in command {}:'.format(context.command), file=sys.stderr)
        traceback.print_exception(type(exception), exception, exception.__traceback__, file=sys.stderr)
        await self.error_channel.send('Ignoring exception in command {}:'.format(context.command) + '\n' +
                                      repr(type(exception)) + ' ' + str(exception) + ': ' + repr(exception.__traceback__))


    async def on_raw_reaction_add(self, payload):
        if payload.emoji.name == '❌':
            id = payload.message_id
            for channel in self.get_all_channels():
                if str(channel.type) == 'text' and channel.id != 510561673971499023:
                    try:
                        message = await channel.fetch_message(id)
                    except (discord.errors.NotFound, discord.errors.Forbidden):
                        pass
                    else:
                        reactions = message.reactions
                        url = message.jump_url
                        contains_x = [r for r in reactions if r.emoji == '❌']
                        if contains_x[0].count == 1 and not self.testmode:
                            title = 'Deletion marked'
                            embed_text = 'Message flagged in <#' + str(message.channel.id) + '>'
                            embed_text += '\n❌ count: ' + str(contains_x[0].count)
                            embed_text += '\n[Jump to message](' + url + ')'

                            image_url = ''
                            attachments = message.attachments
                            if len(attachments) == 0:
                                embed_text += '\n\nNo image provided!'
                            elif len(attachments) == 1:
                                image_url = attachments[0].url
                            elif len(attachments) > 1:
                                embed_text += '\n\nMultiple images provided, jump to message.'

                            embed = discord.Embed(title=title, timestamp=datetime.datetime.utcnow(),
                                                  color=discord.Colour.red(), description=embed_text)
                            if image_url:
                                embed.set_image(url=image_url)
                            footer_text = 'Message ID: ' + str(id)
                            embed.set_footer(text=footer_text)

                            # send new message
                            await self.embed_channel.send(embed=embed)
                        elif contains_x[0].count > 1 and channel.id != 510561673971499023:
                            # fetch old deletion board message
                            messages = await self.embed_channel.history().flatten()
                            try:
                                embed_message = discord.utils.find(lambda m: m.embeds[0].footer.text[-18:] == str(id), messages)
                            except IndexError:
                                await self.error_channel.send(f'Error finding embed for {url}')
                                return
                            if message.channel.id == 510561673971499023 or self.testmode:
                                pass
                            else:
                                embed = embed_message.embeds[0]
                                embed_text = 'Message flagged in <#' + str(message.channel.id) + '>'
                                embed_text += '\n❌ count: ' + str(contains_x[0].count)
                                embed_text += '\n[Jump to message](' + url + ')'

                                image_url = ''
                                attachments = message.attachments
                                if len(attachments) == 0:
                                    embed_text += '\n\nNo image provided!'
                                elif len(attachments) == 1:
                                    image_url = attachments[0].url
                                elif len(attachments) > 1:
                                    embed_text += '\n\nMultiple images provided, jump to message.'

                                new_embed = discord.Embed(title=embed.title, timestamp=embed.timestamp,
                                                      color=embed.colour, description=embed_text)
                                if image_url:
                                    new_embed.set_image(url=image_url)
                                footer_text = 'Message ID: ' + str(id)
                                new_embed.set_footer(text=footer_text)
                                await embed_message.edit(embed=new_embed)

    async def on_error(self, event_method, *args, **kwargs):
        """|coro|

        The default error handler provided by the client.

        By default this prints to :data:`sys.stderr` however it could be
        overridden to have a different implementation.
        Check :func:`~discord.on_error` for more details.
        """

        print('Ignoring exception in {}'.format(event_method), file=sys.stderr)
        traceback.print_exc()
        add_excep = ''.join(traceback.format_exc())
        await self.error_channel.send('Ignoring exception in {}'.format(event_method) + '\n' + add_excep)

    async def on_ready(self, ):
        print(f'{self.user} has connected to Discord!')
        await self.change_presence(activity=discord.Game(name=self.command_prefix + 'help | v' + version))

        self.server = await self.fetch_guild(server_id)
        self.log_channel = self.get_channel(log_channel_id)
        self.join_channel = self.get_channel(joins_id)
        self.kennel_role = self.server.get_role(kenneled_role_id)
        self.muted_role = self.server.get_role(mute_role_id)
        self.me = await self.server.fetch_member(self_id)
        self.error_channel = self.get_channel(error_channel_id)
        self.embed_channel = self.get_channel(starboard_channel)
        self.ban_channel = self.get_channel(ban_channel)
        self.unban_channel = self.get_channel(unban_channel)
        self.carl_channel = self.get_channel(carl_id)
        self.quote_channel = self.get_channel(proto_fun_channel)
        self.timing = 30*60

        self.testmode = testmode
        if self.testmode:
            print('Test mode!')

        await self.quote_channel.send(text_model.make_short_sentence(140))
        self.last_quote_sent = await self.quote_channel.history(limit=1).flatten()[0].created_at

        while True:
            await asyncio.sleep(60)
            await check_reminders()
            if not self.testmode and (datetime.datetime.utcnow() - self.last_quote_sent).total_seconds() > self.timing:
                await self.quote_channel.send(text_model.make_short_sentence(140))
                self.last_quote_sent = await self.quote_channel.history(limit=1).flatten()[0].created_at

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
        if ctx.command:
            highest_role = get_highest_role(ctx.author)
            try:
                if check_permission(highest_role, role_dict, ctx.command.name):
                    await self.invoke(ctx)
                else:
                    if highest_role in role_list:
                        pass
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
        if not self.testmode:
            embed_text = '<@' + str(member.id) + '> ' + member.name + '#' + member.discriminator
            now = datetime.datetime.utcnow()
            delta = now - member.created_at
            s = delta.total_seconds()
            if s < 5*86400:
                duration, _, _, _, _ = duration_text(s)
                embed_text += '\nNew account: created ' + duration
            await self.log_entry(embed_text, title='User Joined', joinleave=True, color=discord.Colour.green(), member=member)

    async def on_member_remove(self, member):
        if not self.testmode:
            embed_text = '<@' + str(member.id) + '> ' + member.name + '#' + member.discriminator
            await self.log_entry(embed_text, title='User Left', joinleave=True, color=discord.Colour.red(), member=member)

    async def on_member_ban(self, guild, member):
        if not self.testmode:
            # wait a bit to ensure a carl log entry
            await asyncio.sleep(5)
            # fetch carl log embed to reproduce responsible moderator
            messages = await self.carl_channel.history(limit=200).flatten()
            log_message = discord.utils.find(lambda m: m.embeds[0].footer.text[-18:] == str(member.id) and 'ban' in m.embeds[0].title, messages)
            embed = log_message.embeds[0]
            # check for temp ban or perm ban
            if embed.title.startswith('ban'):
                type = 'Permanent Ban'
                reason = embed.description.split('\n')[1][12:]
                duration = ''
            elif embed.title.startswith('tem'):
                type = 'Temp Ban'
                duration = embed.description.split('\n')[1][14:]
                reason = embed.description.split('\n')[2][12:]
            # pull moderator
            mod_name = embed.description.split('**Responsible moderator:** ')[1]
            mod = guild.get_member_named(mod_name)
            to_send = '<@' + str(member.id) + '> ' + str(member.id) + ' banned by <@' + str(mod.id) + '>'
            to_send += '\nReason: ' + reason + '\nType: ' + type
            if duration:
                to_send += '\nDuration: ' + duration
            to_send += '\nPlease post evidence for ban below.'
            await self.ban_channel.send(to_send)

    async def on_member_unban(self, guild, member):
        if not self.testmode:
            # wait a bit to ensure a carl log entry
            await asyncio.sleep(5)
            # fetch carl log embed to reproduce responsible moderator
            messages = await self.carl_channel.history(limit=200).flatten()
            log_message = discord.utils.find(lambda m: m.embeds[0].footer.text[-18:] == str(member.id) and 'unban' in m.embeds[0].title, messages)
            embed = log_message.embeds[0]
            reason = embed.description.split('\n')[1][12:]
            to_send = '<@' + str(member.id) + '> ' + str(member.id)
            if 'Automatic unban' in embed.description:
                reason = 'Expiration of temporary ban'
            else:
                # pull moderator
                mod_name = embed.description.split('**Responsible moderator:** ')[1]
                mod = guild.get_member_named(mod_name)
                to_send += ' unbanned by <@' + str(mod.id) + '>'
            to_send += '\nReason: ' + reason
            to_send += '\nPlease post evidence for unban below if appropriate.'
            await self.unban_channel.send(to_send)


# Call custom bot class
bot = CustomBot(command_prefix='$', max_messages=20000)
bot.remove_command('help')
version = '2.4.7'



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
        for rline in lines:
            p = re.compile('\d+\-\d+\-\d+T\d+:\d+\d+:\d+\.\d+')
            iso_time = p.findall(rline)
            if not iso_time:
                pass
            else:
                p = re.compile('\d{18}')
                ids = p.findall(rline)
                if len(ids) < 2:
                    pass
                else:
                    if len(rline) > 65:
                        message = rline[64:].strip('\n')
                    else:
                        message = 'No message given!'
                    try:
                        reminder_date = datetime.datetime.fromisoformat(iso_time[0])
                    except ValueError:
                        try:
                            reminder_date = datetime.datetime.fromisoformat('2' + iso_time[0])
                        except ValueError:
                            try:
                                rline = rline.replace('\x00', '')
                                p = re.compile('\d+\-\d+\-\d+T\d+:\d+\d+:\d+\.\d+')
                                iso_time = p.findall(rline)
                                reminder_date = datetime.datetime.fromisoformat(iso_time[0])
                            except ValueError:
                                reminder_date = datetime.datetime.fromisoformat('20' + iso_time[0])
                    channel = bot.get_channel(int(ids[0]))
                    caller = ids[1]
                    to_send = '<@' + caller + '>: ' + message
                    if reminder_date < datetime.datetime.utcnow():
                        if to_send:
                            await channel.send(to_send)
                    else:
                        await writer(rline)


# Creating command groups
# Misc category
class Misc(commands.Cog, name='Misc.'):
    """Miscellaneous/testing commands!"""
    @bot.command(pass_context=True)
    async def ping(self, ctx):
        """Pong!"""
        start = datetime.datetime.timestamp(datetime.datetime.utcnow())
        msg = await ctx.channel.send('Pinging!')
        await msg.edit(content=f'Pong! ({( datetime.datetime.timestamp( datetime.datetime.utcnow() ) - start ) * 1000 :.2f} ms)')


    @bot.command(pass_context=True)
    async def version(self, ctx):
        """Prints current bot version"""
        await ctx.channel.send('I am currently running on version ' + version + '!')

    @bot.command(pass_context=True)
    async def help(self, ctx):
        """Prints help message"""
        highest_role = get_highest_role(ctx.author)
        to_send = help_message(highest_role, bot.command_prefix)
        print(to_send)
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

    @bot.command(pass_context=True)
    async def timing(self, ctx, duration: int = 0):
        if duration == 0:
            await ctx.channel.send(f'Message timing is every {duration_text(bot.timing, ago=False)[0]}')
        else:
            bot.timing = duration
            to_send = 'Timing updated to every '
            txt, _, _, _, _ = duration_text(duration, ago=False)
            to_send += txt
            await ctx.channel.send(to_send)


# Moderation category
class Moderation(commands.Cog, name='Moderation'):
    """Tools for moderators to use!"""
    @bot.command(pass_context=True)
    async def reminder(self, ctx, *, args=None):
        """Sends a reminder after the given amount of time"""

        args = ''.join(str(i) for i in args)
        time_str = args.split(':')[0].strip()
        args = ':'.join(args.split(':')[1:])
        if time_str.isnumeric():
            duration = int(time_str)
        else:
            time_str = time_str.replace('d', ' days')
            time_str = time_str.replace('m', ' mins')
            time_str = time_str.replace('h', ' hours')
            delta = datetime.datetime.now() - dateparser.parse(time_str)
            duration = delta.total_seconds()

        init_message = 'Sending a reminder in ' + duration_text(duration, ago=False)[0] + '!'
        if args:
            reminder_text = ''.join(str(i) for i in args)
        else:
            reminder_text = ''
        reminder_text = reminder_text.lstrip()
        await add_reminder(ctx, duration, reminder_text=reminder_text)
        await ctx.channel.send(init_message)

    @bot.command(pass_context=True)
    async def kennel(self, ctx, user, *, args=None):
        """Removes all roles from user and adds kennel role!"""
        if args:
            reason = ''.join(str(i) for i in args)
        else:
            reason = 'No reason given'
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
        except (discord.HTTPException, discord.Forbidden):
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
    async def mute(self, ctx, user, *, args=None):
        """Removes all roles from user and adds muted role!"""
        reason = ''.join(str(i) for i in args)
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
    async def warn(self, ctx, type, user, *, args=None):
        """Warn for something!"""
        # get user
        p = re.compile('\d+')
        try:
            user_id = int(p.findall(user)[0])
            user_to_dm = await bot.fetch_user(user_id)
        except IndexError:
            await ctx.channel.send('Invalid format! Put the warning type before the user!')
            return
        needsreminder = True
        if type.lower() == 'nsfw' or type.lower() == 'pfp':
            msg = 'We noticed you have a NSFW profile picture. We do not allow this as it violates Discord ToS. If you don\'' \
                + 't change it within 24 hours we will have no choice but to ban you from the server until you have a SFW '\
                + 'icon. Thanks for understanding ^^ - <@' + str(ctx.author.id) + '> at /r/yiff'
            reason = 'NSFW pfp'
        elif type.lower() == 'hitler':
            msg = 'We noticed you have a rulebreaking profile picture. We do not allow this as it violates server rules on allowable images. If you don\'' \
                  + 't change it within 24 hours we will have no choice but to ban you from the server until you have an acceptable ' \
                  + 'icon. Thanks for understanding ^^ - <@' + str(ctx.author.id) + '> at /r/yiff'
            reason = 'rulebreaking pfp'
        elif type.lower() == 'status':
            msg = 'We noticed you have a rulebreaking Discord status. We do not allow this as it violates server rules on allowable content. If you don\'' \
                  + 't change it within 24 hours we will have no choice but to ban you from the server until you have an acceptable ' \
                  + 'status. Thanks for understanding ^^ - <@' + str(ctx.author.id) + '> at /r/yiff'
            reason = 'status'
        elif type.lower() == 'name' or type.lower() == 'nickname' or type.lower() == 'nick':
            msg = 'We noticed you have a rulebreaking Discord name or nickname. We do not allow this as it violates server rules on allowable content. If you don\'' \
                  + 't change it within 24 hours we will have no choice but to ban you from the server until you have an acceptable ' \
                  + 'name or nickname. Thanks for understanding ^^ - <@' + str(ctx.author.id) + '> at /r/yiff'
            reason = 'name/nickname'
        elif type.lower() == 'custom' or type.lower() == 'warn':
            msg = ''.join(str(i) for i in args)
            reason = msg
            msg = 'You have received a warning from <@' + str(ctx.author.id) + '> in /r/yiff for: ' + msg
            needsreminder = False
        else:
            await ctx.channel.send('Invalid warn type given! Try one of these: `nsfw`, `hitler`, `status`, `name`, `custom`!')
            return
        try:
            await user_to_dm.send(msg)
        except (discord.HTTPException, discord.Forbidden):
            await ctx.channel.send('Could not send DM!')
        else:
            await ctx.channel.send('User ' + user_to_dm.name + '#' + user_to_dm.discriminator + ' notified!')
        embed_text = '<@' + str(
            ctx.author.id) + '> ' + ctx.author.name + '#' + ctx.author.discriminator + ' used `$warn` command on <@'\
            + str(user_id) + '> ' + user_to_dm.name + '#' + user_to_dm.discriminator + '\nReason: ' + reason
        await bot.log_entry(embed_text, title='Command used')
        if needsreminder:
            await add_reminder(ctx, 86400, 'Check on <@' + str(user_to_dm.id) + '>\'s ' + reason + '!')
            await ctx.channel.send('Reminder added!')


# Admin category
class Admin(commands.Cog, name='Administrative'):
    @bot.command(pass_context=True)
    async def reminders(self, ctx):
        with open('reminders.txt', 'rb') as file:
            await ctx.channel.send('Here is the current reminder file!', file=discord.File(fp=file))
        embed_text = '<@' + str(ctx.author.id) + '> ' + ctx.author.name + '#' + ctx.author.discriminator + \
                     ' used `$reminders` command'
        await bot.log_entry(embed_text, title='Command used')

    """toggle test mode"""
    @bot.command(pass_context=True)
    async def test(self, ctx):
        bot.testmode = not bot.testmode
        await ctx.channel.send('Test mode now set to: ' + str(bot.testmode))
        embed_text = '<@' + str(
            ctx.author.id) + '> ' + ctx.author.name + '#' + ctx.author.discriminator + ' used `$test` command, set ' + \
            'test mode to: ' + str(bot.testmode)
        await bot.log_entry(embed_text, title='Command used')

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
        need_year = True
        if args:
            if args[0].isnumeric():
                month = int(args[0])
                if 0 < month < 13:
                    need_month = False
            try:
                if args[1].isnumeric():
                    year = int(args[1])
                    need_year = False
            except IndexError:
                pass
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
                messages = await channel_to_log.history(limit=None).flatten()
                if month >= ctx.message.created_at.month and need_year:
                    year = ctx.message.created_at.year - 1
                    need_year = False
                if need_year:
                    year = ctx.message.created_at.year
                if need_month:
                    month = ctx.message.created_at.month
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
    async def fetchmessage(self, ctx, channel, id):
        channel_to_search = await bot.fetch_channel(channel)
        message = await channel_to_search.fetch_message(id)
        if message.embeds:
            for embed in message.embeds:
                to_send = str(embed.to_dict())
                await ctx.channel.send(to_send)

    @bot.command(pass_context=True)
    async def dm(self, ctx, user):
        user_to_dm = await bot.fetch_user(user)
        try:
            await user_to_dm.send('test dm')
        except (discord.HTTPException, discord.Forbidden):
            await ctx.channel.send('Could not send DM!')
        else:
            await ctx.channel.send('User ' + user_to_dm.name + '#' + user_to_dm.discriminator + ' notified!')

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

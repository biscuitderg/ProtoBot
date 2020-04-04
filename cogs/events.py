import asyncio
import datetime

import discord
from discord.ext import commands

from cogs.utils.loggerEntry import JoinLeave, Ban, Unban
from cogs.utils.modUtils import ModUtils


class Events(commands.Cog, ModUtils):
    def __init__(self, bot):
        super().__init__(bot)
        self.bot = bot
        self.msg_flag_channel = self.get_channel('msg_flag_channel')

    def get_mod(self):
        return self.bot.get_cog("Moderator")

    @commands.Cog.listener()
    async def on_command_completion(self, ctx):
        cmd = ctx.command
        args = ctx.args[2:]
        kwargs = list(ctx.kwargs.values())
        full_args = args + kwargs
        complete_args = []
        try:
            for count, key in enumerate(cmd.clean_params.keys()):
                complete_args.append((key, full_args[count]))
        except IndexError:
            return
        author = ctx.author
        mentioned = ctx.message.mentions
        cog = self.get_mod()
        if cmd.cog == cog:
            embed = discord.Embed(
                title=f'Moderator command used ({cmd.name}):',
                color=discord.Color(0xe62169),
                timestamp=datetime.datetime.utcnow()
            )
            embed.add_field(
                name='Command:',
                value=cmd
            )
            embed.add_field(
                name='User:',
                value=author
            )
            if complete_args:
                embed.add_field(
                    name='Parameters:',
                    value='\n'.join(f'"{a}: {v}"' for a, v in complete_args)
                )
            if mentioned:
                embed.add_field(
                    name='Mentioned/affected users:',
                    value=', '.join([f"{u} ({u.mention})" for u in mentioned])
                )
            channel_id = cog.log_channel
            channel = self.bot.get_channel(channel_id)
            await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        author = payload.member
        emoji = payload.emoji
        channel_id = payload.channel_id
        msg_id = payload.message_id
        channel = self.bot.get_channel(channel_id)
        msg = await channel.fetch_message(msg_id)
        url = msg.jump_url

        if str(emoji) == '❌':
            channel = msg.channel
            if channel.id != 510561673971499023:
                embed = discord.Embed(
                    title=f'Message flagged in {channel}',
                    description=f"[Jump to message]({url})",
                    color=discord.Color(0xe62169),
                    timestamp=datetime.datetime.utcnow()
                )
                if msg.attachments:
                    attachments = msg.attachments
                    embed.set_image(url=attachments[0].url)
                    length = len(attachments)
                    if length > 1:
                        embed.add_field(
                            name=f'There were in total {length} attachments to this message.',
                            value='This was just the first one in the attachments list.'
                        )
                embed.set_footer(text=f"Message ID: {msg_id}")
                await msg.add_reaction('✅')
                log_channel = channel.guild.get_channel(self.msg_flag_channel)
                await log_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        guild = member.guild
        cog = self.get_mod()
        diff = datetime.datetime.utcnow() - member.created_at

        if diff.total_seconds() < 604800:
            acc_created = '{:%b %d, %Y at %I:%M:%S %p} (UTC-0)\n`[Less than one week old]`'.format(member.created_at)
        else:
            acc_created = '{:%b %d, %Y at %I:%M:%S %p} (UTC-0)'.format(member.created_at)

        await cog.log_entry(
            member,
            title='Member Joined',
            description=f"{member} ({member.mention}) has joined the guild.\n"
            f"Account Created: **{acc_created}**\n"
            f"**{guild}** now has **{guild.member_count}** users!\n",
            entry_type=JoinLeave,
            set_thumbnail={"url": member.avatar_url_as(static_format='png')}
        )

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        guild = member.guild
        cog = self.get_mod()
        await cog.log_entry(
            member,
            title='Member Left',
            description=f"**{member}** ({member.mention}) has left the guild.\n"
                        f"**{guild}** now has **{guild.member_count}** users.\n",
            entry_type=JoinLeave,
            set_thumbnail={"url": member.avatar_url_as(static_format='png')}
        )

    @commands.Cog.listener()
    async def on_member_ban(self, guild, member):
        await asyncio.sleep(1)
        cog = self.get_mod()
        async for entry in guild.audit_logs(action=discord.AuditLogAction.ban):
            if entry.target == member:
                resp_user = entry.user
                return await cog.log_entry(
                    member,
                    guild=guild,
                    title="Member Banned",
                    description=f"**{member}** ({member.mention}) was banned from the guild.\n"
                                f"**{guild}** now has **{guild.member_count}** users.\n",
                    entry_type=Ban,
                    set_thumbnail={"url": member.avatar_url_as(static_format='png')},
                    add_field={"name": "Responsible User",
                               "value": f"{resp_user} ({resp_user.mention})",
                               "inline": False}
                )

    @commands.Cog.listener()
    async def on_member_unban(self, guild, member):
        cog = self.get_mod()
        await asyncio.sleep(1)
        async for entry in guild.audit_logs(action=discord.AuditLogAction.unban):
            if entry.target == member:
                resp_user = entry.user
                return await cog.log_entry(
                    member,
                    guild=guild,
                    title='Member Unbanned',
                    description=f"**{member}** ({member.mention}) was unbanned from **{guild}**.",
                    entry_type=Unban,
                    set_thumbnail={"url": member.avatar_url_as(static_format='png')},
                    add_field={"name": "Responsible User",
                               "value": f"{resp_user} ({resp_user.mention})",
                               "inline": False}
                )


def setup(bot):
    bot.add_cog(Events(bot))

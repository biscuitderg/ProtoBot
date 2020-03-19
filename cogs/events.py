import discord
from discord.ext import commands
from cogs.utils.loggerEntry import JoinLeave
from cogs.utils.modUtils import Mod_Utils

import datetime


class Events(commands.Cog, Mod_Utils):
    def __init__(self, bot):
        self.bot = bot
        self.msgflag_channel = self.get_channel('msg_flag_channel')

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
            await msg.remove_reaction('❌', author)
            channel = msg.channel
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
            log_channel = channel.guild.get_channel(self.msgflag_channel)
            await log_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        guild = member.guild
        cog = self.bot.get_cog("Moderator")
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
        cog = self.bot.get_cog("Moderator")
        await cog.log_entry(
            member,
            title='Member Left',
            description=f"**{member}** ({member.mention}) has left the guild.\n"
            f"**{guild}** now has **{guild.member_count}** users.\n",
            entry_type=JoinLeave,
            set_thumbnail={"url": member.avatar_url_as(static_format='png')}
        )


def setup(bot):
    bot.add_cog(Events(bot))
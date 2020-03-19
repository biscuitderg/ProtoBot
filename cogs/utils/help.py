import discord
from discord.ext import commands
from datetime import datetime
from didyoumean import didyoumean as dym


class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.biscuit = 551778995335725063
        self.tauxxy = 570405078498934796
        self.uptime = datetime.utcnow()

    @commands.command()
    async def help(self, ctx, command = None):
        client = self.bot
        author = ctx.author

        if not command:
            embed = discord.Embed(
                    title='Type .help <command> if you would like more info on a command!',
                    description=(
                        'This bot was originally made by <@{}>, ' \
                        'And improved on by <@{}>!'.format(self.biscuit, self.tauxxy)
                    ),
                    color=discord.Color(0xe62169)
                )

            embed.set_author(name=author.display_name, icon_url=author.avatar_url)

            cogs = []
            for name, cog in client.cogs.items():
                commands = [
                    c.name.replace('_', '') 
                    for c in cog.get_commands() 
                    if not c.hidden
                ]
                if not commands:
                    continue
                else:
                    cogs.append((name, '\n'.join(commands), len(commands)))

            cogs.sort(key=lambda key: key[2], reverse=True)
            for name, cmds, _len in cogs:
                embed.add_field(
                    name=f'{name}:',
                    value=cmds
                )

            try:
                await author.send(embed=embed)
                await ctx.send(f'{author.mention} I sent you a list of commands in DMs!')
            except discord.Forbidden:
                await ctx.send(f'{author.mention} I couldn\'t DM you the help list. Please ensure that you have your DMs open and I am not blocked.')
        else:
            command = client.get_command(command)
            try:
                help_msg = help_formatter(command, command.clean_params)
                desc = '```Description: {}```'.format(command.description)
                await ctx.send(help_msg + desc)
            except AttributeError:
                dym.threshold = 1
                output = dym.didYouMean(command, (c.name.replace('_', '') for c in client.commands if not c.hidden))
                await ctx.send(f"That is not a valid command! Did you mean {output}?")


# Help formatter
def help_formatter(cmd, cmd_params):
    params = []
    for key, value in cmd_params.items():
        if str(value).count('=None') == 0:
            params.append(key.replace('_and_', '+').replace('_or_', '/').replace('_', ''))
        else:
            params.append(f"(Optional: {key.replace('_and_', '+').replace('_or_', '/').replace('_', '')})")

    if len(params) > 0:
        return '```Usage: ${} <{}>```'.format(cmd, '> <'.join(params))
    else:
        return '```Usage: ${}```'.format(cmd)


def setup(bot):
    bot.add_cog(Help(bot))
import datetime

import discord
from didyoumean import didyoumean as dym
from discord.ext import commands

from cogs import mod


class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.biscuit = 570405078498934796
        self.tauxxy = 579413130506010654
        self.uptime = datetime.datetime.utcnow()

    @commands.command(description="See what commands you have access to.")
    async def help(self, ctx, command=None):
        """ See what commands you have access to. """
        bot = self.bot
        author = ctx.author
        prefix = ctx.prefix

        if not command:
            embed = discord.Embed(
                title=f'Type help {prefix}<command> if you would like more info on a command!',
                description=(
                    'This bot was originally made by <@{}>, '
                    'And improved on by <@{}>!'.format(self.biscuit, self.tauxxy)
                ),
                color=discord.Color(0xe62169),
                timestamp=datetime.datetime.utcnow()
            )
            embed.set_author(name=author.display_name, icon_url=author.avatar_url)

            final_cmds = {}

            for (cog) in bot.cogs:
                final_cmds[str(cog)] = []
                for command in bot.get_cog(cog).walk_commands():
                    if command not in final_cmds[str(cog)]:
                        if command.parent:
                            continue
                        try:
                            await command.can_run(ctx)
                        except (mod.MissingPermissions, mod.NoAccess):
                            continue
                        else:
                            final_cmds[str(cog)].append(command)

            for cog, cmds in final_cmds.items():
                if len(cmds) > 0:
                    embed.add_field(
                        name=f"**{cog}:**",
                        value="\n".join(f"`{c.qualified_name}:` *{c.description}*" for c in cmds)
                    )

            await ctx.send(embed=embed)
        else:
            command = bot.get_command(command)
            try:
                if command.commands:
                    new_line = "\n"
                    cmds = f'{new_line}'.join([f'   {v}' for v in command.commands])
                    to_send = [
                        command.description,
                        help_formatter(command, command.clean_params),
                        f"Sub-commands:\n{cmds}",
                        'Type "[p]help <command>" for more info on a specific command or sub command.'
                        'i.e. "[p]help warn add" for help on the "add" sub-command of "warn".'
                    ]
                    await ctx.send(f"```{f'{new_line}{new_line}'.join(to_send)}```")
                else:
                    help_msg = help_formatter(command, command.clean_params)
                    desc = '```Description: {}```'.format(command.description)
                    await ctx.send(f"```{help_msg}``` {desc}")
            except AttributeError:
                dym.threshold = 1
                output = dym.didYouMean(command, (c.name.replace('_', '') for c in bot.commands if not c.hidden))
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
        return 'Usage: [p]{} <{}>'.format(cmd, '> <'.join(params))
    else:
        return 'Usage: [p]{}'.format(cmd)


def setup(bot):
    bot.add_cog(Help(bot))

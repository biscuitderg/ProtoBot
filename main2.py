import discord
from discord.ext import commands

import datetime
import os
import json


def get_prefix(client, message):
    with open('./jsons/prefixes.json') as f:
        prefixes = json.load(f)
    try:
        return prefixes[str(message.guild.id)]
    except KeyError:
        set_prefix(message.guild, '$')
        get_prefix(client, message)


def set_prefix(guild, prefix):
    with open('./jsons/prefixes.json') as f:
        prefixes = json.load(f)

    prefixes[str(guild.id)] = prefix

    with open('./jsons/prefixes.json', 'w') as f:
        json.dump(prefixes, f, indent=4)


client = commands.Bot(command_prefix=get_prefix)
token = open('token.txt').read()
owners = [579413130506010654]


def is_owner():
    async def predicate(ctx):
        return ctx.author.id in owners
    return commands.check(predicate)


@client.event
async def on_ready():
    print("Ready.")


@client.event
async def on_command_completion(ctx):
    cmd = ctx.command
    args = ctx.args[2:]
    kwargs = list(ctx.kwargs.values())
    full_args = args + kwargs
    complete_args = []
    for count, key in enumerate(cmd.clean_params.keys()):
        complete_args.append((key, full_args[count]))
    author = ctx.author
    mentioned = ctx.message.mentions
    cog = client.get_cog("Moderator")
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
                value=', '.join([f'{u} "({u.mention})"' for u in mentioned])
            )
        channel_id = cog.log_channel
        channel = client.get_channel(channel_id)
        await channel.send(embed=embed)


@client.command(description='Reloads a cog, or loads if it if it is not instantiated.')
@is_owner()
async def reload(ctx, extension, prefix='cogs'):
    try:
        cog = client.get_cog(extension)
        print(cog)
        if hasattr(cog, 'close'):
            print(True)
            cog.close()
        client.unload_extension(f'{prefix}.{extension}')
        client.load_extension(f'{prefix}.{extension}')
        await ctx.send(f'Cog ``{extension}`` reloaded.')
    except commands.ExtensionNotLoaded:
        client.load_extension(f'{prefix}.{extension}')
        await ctx.send(f'Cog ``{extension}`` loaded.')


for file in os.listdir('./cogs'):
    if file.endswith('.py'):
        client.load_extension(f"cogs.{file[:-3]}")


client.run(token)
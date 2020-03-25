import json
import os

from discord.ext import commands


def get_prefix(bot, message):
    guild = message.guild
    with open("./jsons/prefixes.json") as f:
        prefixes = json.load(f)
    try:
        return prefixes[str(guild.id)]
    except KeyError:
        set_prefix(message.guild, '$')
        get_prefix(bot, message)
    except AttributeError:
        return "$"


def set_prefix(guild, prefix):
    with open('./jsons/prefixes.json') as f:
        prefixes = json.load(f)
    prefixes[str(guild.id)] = prefix
    with open('./jsons/prefixes.json', 'w') as f:
        json.dump(prefixes, f, indent=4)


client = commands.Bot(command_prefix=get_prefix)
client.remove_command("help")
owners = [579413130506010654, 570405078498934796]


def is_owner():
    async def predicate(ctx):
        return ctx.author.id in owners

    return commands.check(predicate)


@client.event
async def on_ready():
    print(f"{client.user.name} is ready.")


for file in os.listdir("./cogs"):
    if file.endswith(".py") and not file.startswith("_"):
        print("Loading {}".format(file))
        client.load_extension(f"cogs.{file[:-3]}")

with open('token.txt') as token:
    client.run(token.read())

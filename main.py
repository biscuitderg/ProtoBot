import os

import discord
import random
import time
from dotenv import load_dotenv
from discord.ext import commands

load_dotenv()

token = os.getenv('DISCORD_TOKEN')

class CustomClient(discord.Client):
    prefix = '$'

    async def on_ready(self):
        print(f'{self.user} has connected to Discord!')
    async def on_message(self, message):
        if message.author == client.user:
            return

        if message.content.lower()[:(len(self.prefix) + 4)] == self.prefix + 'ping':
            await message.channel.send('Pong!')

        if message.content.lower()[:(len(self.prefix) + 8)] == self.prefix + 'reminder':
            args = message.content.lower()[(len(self.prefix) + 9):].split(' ')
            if args:
                try:
                    time.sleep(int(args[0]))
                except ValueError:
                    args = ['', 'Invalid arguments given!']
            if len(args) > 1:
                await message.channel.send(' '.join(args[1:]))

        if message.content.lower()[:8] == '>pfpwarn' and message.channel.id == 575101474032582676:
            try:
                user_to_mention = message.content[9:]
            except IndexError:
                pass
            else:
                if user_to_mention[0] != '<':
                    user_to_mention = '<@' + str(user_to_mention) + '>'
                caller = '<@' + str(message.author.id) + '>'
                time.sleep(86400)
                to_send = str(caller) + ', check on ' + str(user_to_mention) + '\'s profile picture!'
                await message.channel.send(to_send)





client = CustomClient()
client.run(token)

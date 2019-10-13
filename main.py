import os

import discord
import asyncio
from aiofile import AIOFile, LineReader, Writer
import datetime
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

    async def add_reminder(self, message, duration, reminder_text=''):
        async with AIOFile('reminders.txt', 'a+') as reminders:
            writer = Writer(reminders)
            if not reminder_text:
                raw_message = message.content.split(' ')[2:]
            caller_id = message.author.id
            channel_id = message.channel.id
            duration_delta = datetime.timedelta(seconds=duration)
            reminder_date = datetime.datetime.utcnow() + duration_delta
            await writer(reminder_date.isoformat() + ' ' + str(channel_id) + ' ' + str(caller_id) + ' ' + reminder_text + '\n')

    async def check_reminders(self):
        with open('reminders.txt', 'r+') as reminders:
            lines = reminders.readlines()
        async with AIOFile('reminders.txt', 'w+') as reminders:
            writer = Writer(reminders)
            for line in lines:
                items = line.strip('\n').split(' ')
                reminder_date = datetime.datetime.fromisoformat(items[0])
                channel = self.get_channel(int(items[1]))
                caller = items[2]
                to_send = ''
                if len(items) > 3:
                    to_send = '<@' + caller + '>: ' + ' '.join(items[3:])
                if reminder_date < datetime.datetime.utcnow():
                    if to_send:
                        await channel.send(to_send)
                else:
                    await writer(line)


    async def on_message(self, message):
        await self.check_reminders()

        if message.author == client.user:
            return

        if message.content.lower()[:(len(self.prefix) + 4)] == self.prefix + 'ping':
            await message.channel.send('Pong!')

        if message.content.lower()[:(len(self.prefix) + 8)] == self.prefix + 'reminder':
            args = message.content.lower()[(len(self.prefix) + 9):].split(' ')
            if args:
                if args[0].isnumeric():
                    await asyncio.sleep(1)
                    init_message = 'Sending a reminder in ' + args[0] + ' seconds!'
                    if len(args) > 1:
                        reminder_text = ' '.join(args[1:])
                    else:
                        reminder_text = ''
                    await self.add_reminder(message, int(args[0]), reminder_text=reminder_text)
                    await message.channel.send(init_message)
                else:
                    await message.channel.send('Invalid arguments given!')

        if message.content.lower().startswith('>pfpwarn') and message.channel.id == 575101474032582676:
            try:
                user_to_mention = message.content.split(' ')[1]
            except IndexError:
                pass
            else:
                if user_to_mention[0] != '<':
                    user_to_mention = '<@' + str(user_to_mention) + '>'
                caller = '<@' + str(message.author.id) + '>'
                init_message = 'Sending a reminder for checking on ' + user_to_mention + ' in 24 hours!'
                await message.channel.send(init_message)
                to_send = 'Check on ' + str(user_to_mention) + '\'s profile picture!'
                await self.add_reminder(message, duration=86400, reminder_text=to_send)





client = CustomClient()
client.run(token)

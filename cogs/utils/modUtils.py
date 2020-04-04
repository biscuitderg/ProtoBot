import asyncio
import datetime
import json
import math
import random
import re
from sqlite3 import OperationalError

import discord

from cogs.utils.database import Database
from cogs.utils.loggerEntry import LoggerEntry, RoleUpdate


class ModUtils:
    """ Utils for the Moderator cog, to clean up that file. """

    def __init__(self, bot):
        """
        I would put all the channel IDs into a dict for their respective attrs and IDs but
        I don't feel like dealing with instance errors
        """
        self.bot = bot
        self.pagination_amt = 5
        self.scrape_channel = self.get_channel('scrape_channel')
        self.kenneled_role = self.get_channel('kenneled_role')
        self.muted_role = self.get_channel('muted_role')
        self.log_channel = self.get_channel('log_channel')
        self.error_channel = self.get_channel('error_channel')
        self.kennel_channel = self.get_channel('kennel_channel')
        self.joins_channel = self.get_channel('joins_channel')
        self.starboard_channel = self.get_channel('starboard_channel')
        self.ban_channel = self.get_channel('ban_channel')
        self.unban_channel = self.get_channel('unban_channel')
        self.db = Database('./dbs/moderator.db')

    async def ensure_tables(self):
        await self.db.ensure(
            """
            CREATE TABLE IF NOT EXISTS muted
            (user string,
            role string,
            UNIQUE(user, role))
            """,
            """
            CREATE TABLE IF NOT EXISTS warns
            (id string,
            user string,
            issuer string,
            reason string,
            date timestamp DEFAULT CURRENT_TIMESTAMP)
            """,
            """
            CREATE TABLE IF NOT EXISTS kenneled
            (user string,
            role string,
            UNIQUE(user, role))
            """
        )

    @property
    def now(self):
        return datetime.datetime.utcnow()

    @staticmethod
    def strptime(date):
        return datetime.datetime.strptime(date, "%Y-%m-%d %H:%M:%S")

    @classmethod
    def get_config(cls, file):
        """ Fetch data from a configuration JSON file. """
        with open(f'./jsons/{file}.json') as f:
            config = json.load(f)
        return config

    @classmethod
    def set_config(cls, file, param, value):
        """ Edit data in a configuration JSON file. """
        config = cls.get_config(file)
        config[param] = value
        with open(f'./jsons/{file}.json', 'w') as f:
            json.dump(config, f, indent=4)

    @classmethod
    def get_channel(cls, param):
        channels = cls.get_config('channels')
        try:
            channel = channels[param]
            if channel is None:
                raise KeyError
            else:
                return channel
        except KeyError:
            return channels['LoggerEntry_channel']

    @classmethod
    def get_role(cls, param):
        roles = cls.get_config('roles')
        return roles[param]

    async def get_user(self, user_id):
        user_id = int(user_id)
        user = self.bot.get_user(user_id)
        if user is None:
            return await self.bot.fetch_user(user_id)
        else:
            return user

    async def _edit_roles(self, ctx, role, user):
        if role in user.roles:
            reason = f'Changed roles for {user}, -{role.name}'
            await user.remove_roles(
                role,
                reason=f'Role removal requested by {ctx.author}'
            )
        else:
            reason = f'Changed roles for {user}, +{role.name}'
            await user.add_roles(
                role,
                reason=f'Role add requested by {ctx.author}'
            )
        await self.log_entry(ctx, text=reason, entry_type=RoleUpdate, title='Role update')

    async def paginate(self, msg, author, embed):
        """ Paginate across an embed. """
        emoji_list = ['⏪', '⬅️', '➡️', '⏩']
        footer = embed.footer.text
        pattern = re.compile(r'.*?(\d+).*?(\d+)')
        match = pattern.match(footer)
        page = int(match.group(1))
        end = int(match.group(2))

        for reaction in emoji_list:
            await msg.add_reaction(reaction)

        def check(r, u):
            return u == author and r.emoji in emoji_list

        try:
            reaction, user = await self.bot.wait_for(
                'reaction_add',
                timeout=180.0,
                check=check
            )
            await reaction.remove(author)
        except asyncio.TimeoutError:
            await msg.delete()
        else:
            if reaction.emoji == '⏪':
                await self._paginate(*[msg, author, embed], 1)
            elif reaction.emoji == '⬅️':
                await self._paginate(*[msg, author, embed], page - 1)
            elif reaction.emoji == '➡️':
                await self._paginate(*[msg, author, embed], page + 1)
            else:
                await self._paginate(*[msg, author, embed], end)

    async def _paginate(self, msg, author, embed, page):
        total = math.ceil(len(embed.fields) / self.pagination_amt)
        if (page > total) or (page == 0):
            return await self.paginate(msg, author, embed)
        else:
            embed.set_footer(text=f"Page {page} of {total}")
            _embed = embed.copy()
            start = (page - 1) * self.pagination_amt
            end = start + self.pagination_amt
            em_dict = _embed.to_dict()
            em_dict["fields"] = em_dict["fields"][start:end]
            await msg.edit(embed=discord.Embed.from_dict(em_dict))
            await self.paginate(msg, author, embed)

    @LoggerEntry.converter
    async def log_entry(self,
                        ctx,
                        *,
                        guild=None,
                        title=None,
                        description=None,
                        entry_type: LoggerEntry.check,
                        **kwargs):
        """ Adds an entry to ProtoBot logs """
        if guild is None:
            guild = ctx.guild
        color = guild.me.color
        embed = discord.Embed(
            title=title,
            description=description,
            color=color,
            timestamp=self.now,
        )
        if entry_type:
            embed.set_author(
                name=f"New {entry_type()} Event Occurred:"
            )
        for k, v in kwargs.items():
            # equivalent to "embed.set_{k}(v[key]=v[value])"
            getattr(embed, k)(**v)  # for example "embed.set_description(url=<url>)"

        _channel = self.get_channel(entry_type().channel)
        channel = guild.get_channel(int(_channel))
        await channel.send(embed=embed)

    async def generate_id(self):
        """ Generates a random ID to use - Ensures no other entry has the same ID """
        random_number = random.randint(0, 65536)
        _id = str(hex(random_number))[2:]
        if await self.id_exists(_id):
            return await self.generate_id()
        else:
            return _id

    async def id_exists(self, _id):
        """ Checks if ID exists already in database. """
        try:
            return await self.db.search("warns", id=_id)
        except OperationalError:
            return False

    async def fetch_user_warns(self, user):
        """
        Fetches all warns under a specified user.
        
        Parameters
        ------------
        user: :class:`discord.Member`
            The user to look up warns for
        
        Returns
        ------------
        params: [:class:`str`]
            [ID, author, reason, date]
        """

        return await self.db.getall(
            "SELECT id, issuer, reason, date FROM warns WHERE user=?",
            (user.id,)
        )

    async def fetch_warn(self, identifier):
        """
        Fetches a warn using the specified ID.
        
        Parameters
        ------------
        identifier: :class:`int`
            The ID to look for
        
        Returns
        ------------
        params: [:class:`str`]
            [user, author, reason, date]
        """

        return await self.db.get(
            "SELECT user, issuer, reason, date FROM warns WHERE id=?",
            (identifier,)
        )

    async def change_warn(self, identifier, reason):
        """
        Change the reason of a warn using the specified ID.
        
        Parameters
        ------------
        identifier: :class:`int`
            The ID to look for
        reason: :class:`str`
            The new reason to enter into the warn
        
        Returns
        ------------
        :class:`bool`
            Whether the specified warn was found and edited.
        """

        if await self.fetch_warn(identifier):
            await self.db.execute(
                "UPDATE warns SET reason=? WHERE id=?",
                (reason, identifier)
            )
            return True
        else:
            return False

    async def delete_warn(self, identifier):
        """
        Deletes a warn using the specified ID.
        
        Parameters
        ------------
        identifier: :class:`int`
            The ID to look for
        
        Returns
        ------------
        :class:`bool`
            Whether the specified warn was deleted.
        """

        before = bool(await self.fetch_warn(identifier))
        await self.db.get(
            "DELETE FROM warns WHERE id=?",
            (identifier,)
        )
        after = bool(await self.fetch_warn(identifier))
        if before == after:
            return False
        else:
            return True

    async def log_warn(self, identifier, user, author, reason):
        """
        Logs a warn for the specified user.
        
        Parameters
        ------------
        identifier: :class:`str`
            The warn ID to log it for
        user: :class:`discord.Member`
            The user to log the warn for
        author: :class:`discord.Member`
            The issuer of the warn
        reason: :class:`str`
            The reason to log
        """

        await self.db.execute(
            "INSERT INTO warns (id, user, issuer, reason) VALUES (?, ?, ?, ?)",
            (identifier, user.id, author.id, reason)
        )

    async def is_kenneled(self, user):
        """
        Check if the user is kenneled.
        
        Parameters
        ------------
        user: :class:`discord.Member`
            The user to check for
        
        Returns
        ------------
        :class:`bool`
            If the user is kenneled or not.
        """
        
        return await self.db.search(
            "kenneled", user=user.id
        )

    async def is_muted(self, user):
        """
        Check if the user is muted.
        
        Parameters
        ------------
        user: :class:`discord.Member`
            The user to check for
        
        Returns
        ------------
        :class:`bool`
            If the user is muted or not.
        """

        return await self.db.search(
            "muted", user=user.id
        )

    async def add_kenneled(self, user, roles):
        """
        Add this user to the kenneled database.

        Parameters
        -----------
        user: :class:`discord.Member`
            The user to add.
        roles: [:class:`discord.Role`]
            The role(s) to add.
        """

        if len(roles) > 0:
            await self.db.executemany(
                "INSERT INTO kenneled (user, role) VALUES (?, ?)",
                ([(user.id, r.id) for r in roles])
            )
        else:
            await self.db.execute(
                "INSERT INTO kenneled (user, role) VALUES (?, ?)",
                (user.id, 0)
            )

    async def add_muted(self, user, roles):
        """
        Add this user to the muted database.

        Parameters
        -----------
        user: :class:`discord.Member`
            The user to add.
        roles: [:class:`discord.Role`]
            The role(s) to add.
        """

        if len(roles) > 0:
            await self.db.executemany(
                "INSERT INTO muted (user, role) VALUES (?, ?)",
                ([(user.id, r.id) for r in roles])
            )
        else:
            await self.db.execute(
                "INSERT INTO muted (user, role) VALUES (?, ?)",
                (user.id, 0)
            )

    async def remove_kenneled(self, user):
        """
        Remove this user from the kenneled database.

        Parameters
        ------------
        user: :class:`discord.Member`

        Returns
        --------
        [:class:`int`]
            The roles to add back, if the user is kenneled.
        :class:`NoneType`
            If the user was not found to be kenneled.
        """

        roles = await self.db.getall(
            "SELECT role FROM kenneled WHERE user=?",
            (user.id,)
        )
        await self.db.execute(
            "DELETE FROM kenneled WHERE user=?",
            (user.id,)
        )
        if roles:
            return [r[0] for r in roles]  # stupid sqlite returns a one-tuple for each row, soo
        else:
            return None

    async def remove_muted(self, user):
        """
        Remove this user from the muted database.

        Parameters
        ------------
        user: :class:`discord.Member`

        Returns
        --------
        [:class:`int`]
            The roles to add back, if the user is muted.
        :class:`NoneType`
            If the user was not found to be muted.
        """

        roles = await self.db.getall(
            "SELECT role FROM muted WHERE user=?",
            (user.id,)
        )
        await self.db.execute(
            "DELETE FROM muted WHERE user=?",
            (user.id,)
        )
        if roles:
            return [r[0] for r in roles] # stupid sqlite returns a one-tuple for each row, soo
        else:
            return None

    async def get_kenneled_roles(self, user):
        """
        Get current roles of kenneled user.

        Parameters
        ------------
        user: :class:`discord.Member`

        Returns
        --------
        [:class:`int`]
            The roles the user had.
        :class:`NoneType`
            If the user was not found to be kenneled.
        """

        return await self.db.getall(
            "SELECT role FROM kenneled WHERE user=?",
            (user.id,)
        )

    async def get_muted_roles(self, user):
        """
        Get current roles of muted user.

        Parameters
        ------------
        user: :class:`discord.Member`

        Returns
        --------
        [:class:`int`]
            The roles the user had.
        :class:`NoneType`
            If the user was not found to be muted.
        """

        return await self.db.getall(
            "SELECT role FROM muted WHERE user=?",
            (user.id,)
        )

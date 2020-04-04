import asyncio

import cogs.utils.asqlite as asqlite


class Database:
    def __init__(self, connection):
        self.loop = asyncio.get_event_loop()
        self.conn = self.loop.run_until_complete(asqlite.connect(connection))
        self.cursor = self.conn.cursor()

    async def ensure(self, *statements):
        """ Ensures tables exist, etc. """
        for s in statements:
            await self.execute(s)

    async def search(self, table, **kwargs):
        """
        Search for if a data pair exists in inputted table. Returns boolean of if found.
        """
        clauses = " AND ".join([f"{k} = {v}" for k, v in kwargs.items()])
        return await self.get(
            f"SELECT * FROM {table} WHERE {clauses}"
        )

    async def get(self, resp, args=()):
        """
        Selects 1 row matching provided resp and optional args.
        
        Returns value if len(row) == 1 else :class:`tuple`(*args)
        Returns None if none found.
        """
        async with self.cursor as c:
            await c.execute(resp, args)
            row = await c.fetchone()
            if row:
                _row = tuple(row)
                return _row[0] if len(_row) == 1 else _row
            else:
                return None

    async def getall(self, resp, args=()):
        """
        Generator for all rows matching provided response and optional args.
        
        Returns a :class:`list` of all entires, or `None` if nothing found.
        """
        async with self.cursor as c:
            await c.execute(resp, args)
            rows = await c.fetchall()
            if rows:
                return [tuple(r) for r in rows]
            else:
                return None

    async def execute(self, resp, args=()):
        """ Modifies data in rows, and returns any returned rows. """
        async with self.cursor as c:
            await c.execute(resp, args)
            return await c.fetchall()

    async def executemany(self, resp, args=[()]):
        """ Modifies data using `executemany`, and returns any returned rows. """
        async with self.cursor as c:
            await c.executemany(resp, args)
            return await c.fetchall()

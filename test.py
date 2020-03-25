import asyncio
import json
import time

from aiofile import AIOFile, Reader


async def mycoro():
    with open('r.txt') as f:
        data = json.load(f)

    print("Finished 1:", data)


async def mycoro2():
    t = time.time()
    data = []
    _dicts = []
    async with AIOFile("r.txt") as f:
        line_reader = Reader(f)
        async for chunk in line_reader:
            print(chunk)
            '''
            if len(chunk.strip()) > 1:
                print(chunk.strip()[:-1])
                data.append(json.loads(chunk.strip()[:-1]))
            '''


async def main():
    await asyncio.gather(
        asyncio.ensure_future(mycoro()),
        asyncio.ensure_future(mycoro2())
    )


loop = asyncio.get_event_loop()
loop.run_until_complete(main())
loop.close()

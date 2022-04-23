import asyncio
from typing import Any, OrderedDict

import trio
from pytest import mark

from alleycat.event import CoroutineRunner


@mark.asyncio
async def test_coroutine_runner():
    events = []

    async def callback():
        events.append(1)

        await trio.sleep(0.1)
        events.append(2)

        await trio.sleep(0.1)
        events.append(3)

    runner = CoroutineRunner()

    runner.update()
    runner.run_async(callback)

    for _ in range(1, 10):
        runner.update()
        await asyncio.sleep(0.1)

    assert events == [1, 2, 3]

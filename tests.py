import asyncio
from functools import partial
from unittest import mock

import pytest

from asyncio_monkey import (
    PY_360, patch_all, patch_log_destroy_pending, patch_get_event_loop,
)


def create_task(*, loop=None):
    if loop is None:
        loop = asyncio.get_event_loop()

    try:
        return loop.create_task
    except AttributeError:
        try:
            return partial(asyncio.ensure_future, loop=loop)
        except AttributeError:
            return partial(getattr(asyncio, 'async'), loop=loop)


def test_patch_log_destroy_pending():
    assert not hasattr(asyncio.Task, 'patched')

    loop = asyncio.get_event_loop()

    @asyncio.coroutine
    def corofunction():
        pass

    coro = corofunction()
    task = create_task()(coro)

    assert task._log_destroy_pending

    task._log_destroy_pending = False

    assert not task._log_destroy_pending

    task.cancel()

    ###

    patch_log_destroy_pending()
    patch_log_destroy_pending()

    ###

    assert hasattr(asyncio.Task, 'patched')

    coro = corofunction()
    task = create_task()(coro)

    assert task._log_destroy_pending

    task._log_destroy_pending = False

    assert task._log_destroy_pending

    task.cancel()

    loop.close()


def test_get_event_loop():
    if not PY_360:
        return

    @asyncio.coroutine
    def coro():
        loop = asyncio.get_event_loop()

        return loop

    asyncio.set_event_loop(None)

    loop = asyncio.new_event_loop()

    ###

    assert not hasattr(asyncio.get_event_loop, 'patched')

    running_loop = loop.run_until_complete(coro())

    assert running_loop is loop

    ###

    patch_get_event_loop()
    patch_get_event_loop()

    ###

    assert hasattr(asyncio.get_event_loop, 'patched')

    with pytest.raises(RuntimeError):
        loop.run_until_complete(coro())

    ###

    loop.close()


def test_patch_all():
    with mock.patch('asyncio_monkey.patch_get_event_loop') as mocked_patch_get_event_loop, mock.patch('asyncio_monkey.patch_log_destroy_pending') as mocked_patch_log_destroy_pending:  # noqa

        patch_all()

        assert mocked_patch_get_event_loop.called_once()
        assert mocked_patch_log_destroy_pending.called_once()

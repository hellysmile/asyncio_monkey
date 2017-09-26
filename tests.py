import asyncio

from asyncio import test_utils
from functools import partial
from unittest import mock

import pytest
from asyncio_monkey import (
    PY_360, PY_362, patch_all, patch_get_event_loop,
    patch_lock, patch_log_destroy_pending,
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


def test_no_patch_lock():
    if PY_362:
        return

    loop = asyncio.new_event_loop()

    assert not hasattr(asyncio.Lock, 'patched')
    assert not hasattr(asyncio.locks.Lock, 'patched')

    lock = asyncio.Lock(loop=loop)

    ta = asyncio.Task(lock.acquire(), loop=loop)
    test_utils.run_briefly(loop)
    assert lock.locked()

    tb = asyncio.Task(lock.acquire(), loop=loop)
    test_utils.run_briefly(loop)
    assert len(lock._waiters) == 1

    # Create a second waiter, wake up the first, and cancel it.
    # Without the fix, the second was not woken up.
    tc = asyncio.Task(lock.acquire(), loop=loop)
    lock.release()
    tb.cancel()
    test_utils.run_briefly(loop)

    assert not lock.locked()
    assert ta.done()
    assert tb.cancelled()

    loop.close()


def test_patch_lock():
    loop = asyncio.new_event_loop()

    assert not hasattr(asyncio.Lock, 'patched')
    assert not hasattr(asyncio.locks.Lock, 'patched')

    patch_lock()
    patch_lock()

    assert hasattr(asyncio.Lock, 'patched')
    assert hasattr(asyncio.locks.Lock, 'patched')

    lock = asyncio.Lock(loop=loop)

    ta = asyncio.Task(lock.acquire(), loop=loop)
    test_utils.run_briefly(loop)
    assert lock.locked()

    tb = asyncio.Task(lock.acquire(), loop=loop)
    test_utils.run_briefly(loop)
    assert len(lock._waiters) == 1

    # Create a second waiter, wake up the first, and cancel it.
    # Without the fix, the second was not woken up.
    tc = asyncio.Task(lock.acquire(), loop=loop)
    lock.release()
    tb.cancel()
    test_utils.run_briefly(loop)

    # tc waiter acquired lock
    assert lock.locked()
    assert ta.done()
    assert tb.cancelled()

    loop.close()


def test_patch_all():
    with mock.patch('asyncio_monkey.patch_get_event_loop') as mocked_patch_get_event_loop, \
            mock.patch('asyncio_monkey.patch_log_destroy_pending') as mocked_patch_log_destroy_pending, \
                mock.patch('asyncio_monkey.patch_lock') as mocked_patch_lock:  # noqa

        patch_all()

        assert mocked_patch_get_event_loop.called_once()
        assert mocked_patch_log_destroy_pending.called_once()
        assert mocked_patch_lock.called_once()

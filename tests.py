import asyncio
import os
from asyncio import test_utils
from unittest import mock

import pytest
from asyncio_monkey import (
    PY_353, PY_362, patch_all, patch_gather, patch_get_event_loop,
    patch_lock, patch_log_destroy_pending, _ensure_future
)


@pytest.fixture
def loop(request):
    asyncio.set_event_loop(None)

    loop = asyncio.new_event_loop()

    loop.set_debug(bool(os.environ.get('PYTHONASYNCIODEBUG')))

    request.addfinalizer(lambda: asyncio.set_event_loop(None))

    yield loop

    loop.call_soon(loop.stop)

    loop.run_forever()

    loop.close()


def test_patch_log_destroy_pending(loop):
    assert not hasattr(asyncio.Task, 'patched')

    @asyncio.coroutine
    def corofunction():
        pass

    coro = corofunction()
    task = _ensure_future(loop=loop)(coro)

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
    task = _ensure_future(loop=loop)(coro)

    assert task._log_destroy_pending

    task._log_destroy_pending = False

    assert task._log_destroy_pending

    task.cancel()


def test_get_event_loop(loop):
    if not PY_353:
        return

    @asyncio.coroutine
    def coro():
        return asyncio.get_event_loop()

        return loop

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


def test_no_patch_lock(loop):
    if PY_362:
        return

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


def test_patch_lock(loop):
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


def test_patch_gather(loop):
    assert not hasattr(asyncio.gather, 'patched')
    assert not hasattr(asyncio.tasks.gather, 'patched')

    patch_gather()
    patch_gather()

    assert hasattr(asyncio.gather, 'patched')
    assert hasattr(asyncio.tasks.gather, 'patched')

    counter = 0

    @asyncio.coroutine
    def incr_counter(t):
        nonlocal counter

        yield from asyncio.sleep(t, loop=loop)
        counter += 1

        return counter

    @asyncio.coroutine
    def fail(t):
        yield from asyncio.sleep(t, loop=loop)
        raise ZeroDivisionError

    coros = [incr_counter(.1), incr_counter(.2), fail(0.3), incr_counter(.4)]

    futs = [_ensure_future(loop=loop)(f) for f in coros]

    with pytest.raises(ZeroDivisionError):
        loop.run_until_complete(asyncio.gather(*futs, loop=loop))

    assert counter == 2

    for fut in futs:
        assert fut.done()

    assert futs[0].result() is 1
    assert futs[1].result() is 2

    with pytest.raises(ZeroDivisionError):
        futs[2].result()

    with pytest.raises(asyncio.CancelledError):
        futs[3].result()


def test_patch_all():
    with \
        mock.patch('asyncio_monkey.patch_gather') as mocked_patch_gather, \
        mock.patch('asyncio_monkey.patch_get_event_loop') as mocked_patch_get_event_loop, \
        mock.patch('asyncio_monkey.patch_log_destroy_pending') as mocked_patch_log_destroy_pending, \
        mock.patch('asyncio_monkey.patch_lock') as mocked_patch_lock:  # noqa

        patch_all()

        assert mocked_patch_gather.called_once()
        assert mocked_patch_get_event_loop.called_once()
        assert mocked_patch_log_destroy_pending.called_once()
        assert mocked_patch_lock.called_once()

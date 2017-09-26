__version__ = '0.1.0'


asyncio = None


def _create_future(*, loop=None):
    global asyncio

    if loop is None:
        loop = asyncio.get_event_loop()

    try:
        return loop.create_future()
    except AttributeError:
        if asyncio is None:
            import asyncio as _asyncio
            asyncio = _asyncio
        return asyncio.Future(loop=loop)


def patch_log_destroy_pending():
    import asyncio

    if hasattr(asyncio.tasks.Task, 'patched'):
        return

    class Task(asyncio.tasks.Task):
        patched = True

        def _get_log_destroy_pending(self):
            return True

        def _set_log_destroy_pending(self, value):
            pass

        _log_destroy_pending = property(
            _get_log_destroy_pending,
            _set_log_destroy_pending,
        )

        del _get_log_destroy_pending
        del _set_log_destroy_pending

    asyncio.tasks.Task = Task
    asyncio.Task = asyncio.tasks.Task


def patch_get_event_loop():
    import asyncio

    if hasattr(asyncio.events.get_event_loop, 'patched'):
        return

    def get_event_loop():
        return asyncio.events.get_event_loop_policy().get_event_loop()
    get_event_loop.patched = True

    asyncio.events.get_event_loop = get_event_loop
    asyncio.get_event_loop = asyncio.events.get_event_loop


def patch_lock():
    import asyncio

    if hasattr(asyncio.locks.Lock, 'patched'):
        return

    # Fixes an issue with all Python versions that leaves pending waiters
    # without being awakened when the first waiter is canceled.
    # Code adapted from the PR https://github.com/python/cpython/pull/1031
    # Waiting once it is merged to make a proper condition to relay on
    # the stdlib implementation or this one patched

    class Lock(asyncio.locks.Lock):
        patched = True

        @asyncio.coroutine
        def acquire(self):
            """Acquire a lock.
            This method blocks until the lock is unlocked, then sets it to
            locked and returns True.
            """
            if not self._locked and all(w.cancelled() for w in self._waiters):
                self._locked = True
                return True

            fut = _create_future(loop=self._loop)

            self._waiters.append(fut)
            try:
                yield from fut
                self._locked = True
                return True
            except asyncio.futures.CancelledError:
                if not self._locked:  # pragma: no cover
                    self._wake_up_first()
                raise
            finally:
                self._waiters.remove(fut)

        def _wake_up_first(self):
            """Wake up the first waiter who isn't cancelled."""
            for fut in self._waiters:
                if not fut.done():
                    fut.set_result(True)
                    break

    asyncio.locks.Lock = Lock
    asyncio.Lock = Lock


def patch_all():
    patch_log_destroy_pending()
    patch_get_event_loop()
    patch_lock()

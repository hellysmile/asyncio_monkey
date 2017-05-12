import sys

PY_360 = sys.version_info >= (3, 6, 0)

__version__ = '0.0.1'


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

    if not PY_360:
        return

    def get_event_loop():
        return asyncio.events.get_event_loop_policy().get_event_loop()
    get_event_loop.patched = True

    asyncio.events.get_event_loop = get_event_loop
    asyncio.get_event_loop = asyncio.events.get_event_loop


def patch_all():
    patch_log_destroy_pending()
    patch_get_event_loop()

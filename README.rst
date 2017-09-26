asyncio_monkey
==============

:info: monkey patch asyncio modules for expected behaviour

.. image:: https://img.shields.io/travis/wikibusiness/asyncio_monkey.svg
    :target: https://travis-ci.org/wikibusiness/asyncio_monkey

.. image:: https://img.shields.io/pypi/v/asyncio_monkey.svg
    :target: https://pypi.python.org/pypi/asyncio_monkey

Installation
------------

.. code-block:: shell

    pip install asyncio_monkey

Usage
-----

.. code-block:: python

    # it must be done before any import asyncio statement, once per project
    # best place is __init__.py of You'r application
    from asyncio_monkey import patch_all  # noqa isort:skip
    patch_all()

or call the one you need

.. code-block:: python

    # it must be done before any import asyncio statement, once per project
    # best place is __init__.py of You'r application
    import asyncio_monkey  # noqa isort:skip

    asyncio_monkey.patch_gather()
    asyncio_monkey.patch_log_destroy_pending()
    asyncio_monkey.patch_get_event_loop()
    asyncio_monkey.patch_lock()

Features
--------

- Cancel pending tasks `gather` if any task fails, `source <https://bugs.python.org/issue31452>`_

- Disables `get_event_loop` returns currently running loop, even if `MainThread` loop is `None`, `docs <https://docs.python.org/3/library/asyncio-eventloops.html#asyncio.get_event_loop>`_ , `source <https://bugs.python.org/issue28613>`_

- Disables silent destroying futures inside `asyncio.gather` `source <https://github.com/python/cpython/blob/3dc7c52a9f4fb83be3e26e31e2c7cd9dc1cb41a2/Lib/asyncio/tasks.py#L600>`_

- Prevents `asyncio.Lock` deadlock after cancellation  `source <http://bugs.python.org/issue27585>`_

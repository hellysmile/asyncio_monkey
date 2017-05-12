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

    # it must be done before any import asyncio statement
    from asyncio_monkey import patch_all; patch_all()  # noqa

Features
--------

- Disables `get_event_loop` returns currently running loop, even if `MainThread` loop is `None`, useful for Python 3.6.0+ `docs <https://docs.python.org/3/library/asyncio-eventloops.html#asyncio.get_event_loop>`_

- Disables silent destroying futures inside `asyncio.gather` `source <https://github.com/python/cpython/blob/3dc7c52a9f4fb83be3e26e31e2c7cd9dc1cb41a2/Lib/asyncio/tasks.py#L600>`_

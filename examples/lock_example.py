"""Graceful shutdown, an example use case for :class:`~toro.Lock`.

``poll`` continuously fetches http://tornadoweb.org, and after 5 seconds,
``shutdown`` stops the IOLoop. We want any request that ``poll`` has begun to
complete before the loop stops, so ``poll`` acquires the lock before starting
each HTTP request and releases it when the request complets. ``shutdown`` also
acquires the lock before stopping the IOLoop.

(Inspired by a post_ to the Tornado mailing list.)

.. _post: https://groups.google.com/d/topic/python-tornado/CXg5WwufOvU/discussion
"""

# start-file
import datetime
from tornado import ioloop, gen, httpclient
import toro

lock = toro.Lock()
loop = ioloop.IOLoop.instance()

@gen.engine
def poll():
    client = httpclient.AsyncHTTPClient()
    while True:
        yield gen.Task(lock.acquire)
        try:
            print 'Starting request'
            response = yield gen.Task(client.fetch, 'http://www.tornadoweb.org/')
            print response.code
        finally:
            lock.release()

        # Wait a tenth of a second before next request
        yield gen.Task(loop.add_timeout, datetime.timedelta(seconds=0.1))

@gen.engine
def shutdown():
    # Get the lock: this ensures poll() isn't in a request when we stop the
    # loop
    print 'shutdown() is acquiring the lock'
    yield gen.Task(lock.acquire)
    loop.stop()
    print 'Loop stopped.'


if __name__ == '__main__':
    # Start polling
    poll()

    # Arrange to shutdown cleanly 5 seconds from now
    loop.add_timeout(datetime.timedelta(seconds=5), shutdown)
    loop.start()

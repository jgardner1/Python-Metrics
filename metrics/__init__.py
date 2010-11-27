"""Logging facilities for metrics.

Metrics represent instaneous event and their attached data, or events that
take a duration.

Each event has the following mandatory attributes:

    - context: The context of the event.

    - start: The time when it started, in seconds since epoch. (As returned by
      time.time()

    - name: A unique name to identify the event. This name is really more of a
      type. Within a context, an event name need not be unique.

    - misc. attributes: These attributes may include things like "duration"
      which records how long the event took.

Contexts describe the overall context of an event. This would include things
like important request data and such. All events occur within a specific
context.
"""
import json
from time import time
import threading
import logging

log = logging.getLogger(__name__)

context = threading.local()

def event(name, **kw):
    """Register an event in the threadlocal context, if any.

    'name' is required and need not be unique. It should describe the event
    type.

    'start' is set if not specified to the current time.
    """
    kw.setdefault('start', time())
    kw['name'] = name
    events = getattr(context, 'events', None)
    if events is None:
        log.warn("%s: no context to record event: %r" % (
            threading.current_thread().name, kw))
    else:
        events.append(kw)

class Timer(object):
    """A Timer to use with the 'with' statement.

    with Timer(foo=5) as t:
        t['results'] = 17

    The context object is actually a dictionary, and you can change or set
    values that will show up in the metric output.

    The event is registered in the threadlocal context, if any, once it
    completes.
    """

    def __init__(self, name, **kw):
        self.name = name
        self.kw = kw

    def __enter__(self):
        self.start = time()
        return self.kw

    def __exit__(self, exc_type, exc_value, traceback):
        self.kw.update(dict(
            name     = self.name,
            start    = self.start,
            duration = time()-self.start))
        event(**self.kw)

class Context(object):
    """Creates a global, threadlocal context for all events with the 'with'
    statement.

    with Context(foo=5) as c:
        c['session_id'] = session.id

    Note that libraries do not need access to the context in the with
    statement. They will have access through a threadlocal variable.
    """

    def __init__(self, **kw):
        self.kw = kw
        self.events = []

    def __enter__(self):
        self.start = time()
        context.old_context = dict(
                kw=getattr(context, 'kw', None),
                events=getattr(context, 'events', None),
                old_context=getattr(context, 'old_context', None))
        context.events = self.events
        context.kw = self.kw
        log.debug("%s: entering new context, replacing %r" % (
            threading.current_thread().name,
            context.old_context['kw'],))

        return self.kw

    def __exit__(self, exc_type, exc_value, traceback):
        context.kw = context.old_context['kw']
        context.events = context.old_context['events']
        context.old_context = context.old_context['old_context']

        self.kw.update(dict(
            events=self.events,
            start=self.start,
            duration=time()-self.start))
        log.info(json.dumps(self.kw))

        log.debug("%s: leaving context" % (
            threading.current_thread().name,))

class MetricsContextApp(object):
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        with Context(
                REMOTE_ADDR  = environ['REMOTE_ADDR'],
                PATH_INFO    = environ['PATH_INFO'],
                QUERY_STRING = environ['QUERY_STRING'],
                thread       = threading.current_thread().name,
        ) as c:
            environ['metrics_context'] = c
            return self.app(environ, start_response)

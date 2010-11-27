"""Logging facilities for metrics.

This module is used for recording, at a much higher-grain level than
performance analyzing software, the large-scale behavior of your system. For
instance, let's say you run a script every 5 minutes and you want to know how
long it takes for each step, how many records are manipulated, and what the
sum totals are for each operation. Or, you run a website and you want to know
how long each request takes, as well as where each request originated from in
addition to the session ID or user ID of the request.

To record metrics, you must first setup a METRICS CONTEXT. This is an object
that records numbers and times for the entire operation. Contexts are not
nestable, so make sure you only setup one context for the entire operation.
This could be a single request, an entire run of a thread, or a complete
script execution.

To setup a metrics context, simply do:

    import metrics

    with Context() as c:
        ...

Note that contexts take name-value pairs, which you can pass in the
constructor or set with the 'c' object, which is a dict.

Once you have a context setup, you can record events. There are, roughly, two
types of events:

    * Instaneous events, occurring at an instance in time.
    * Duration events, occurring over a period of time.

To record any event, you can use the 'event' method, passing in a name and the
keywords you want to us. 'start' is always used and records when the event
started. For instaneous events, there is no 'duration' specified, which is how
long the event took.

To make recording events with duractions, the 'Timer' class can be used.

    with Timer() as t:
        ...

The start time is when the timer was created---before the block of code inside
the with statement is run. Like the Context object, you can specify keywords
in the constructor of the Timer or by manipulating the 't' dictionary.

If you are using a web app with WSGI, you can use the MetricsContextApp which
will setup a context for every request that passes through it, setting key
keywords.

The metrics are output using the logger with the name 'metrics' at log level
'info'. To parse the logs, extract the JSON data from each line. No parsing
support is provided with this module.
"""
import json
from time import time
import threading
import logging

log = logging.getLogger(__name__)

# The global, threadlocal context
context = threading.local()

def event(name, **kw):
    """Register an event in the threadlocal context, if any.

    'name' is required and need not be unique. It should describe the event
    type.

    'start' is set if not specified to the current time.

    Other keyword arguments can be used to taste.
    """
    events = getattr(context, 'events', None)
    if events is None:
        log.warn("%s: no context to record event: %r" % (
            threading.current_thread().name, kw))
    else:
        if 'start' not in kw:
            kw['start'] = time()
        kw['name'] = name
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
    statement. They will have access through a threadlocal global variable.
    """

    def __init__(self, **kw):
        self.kw = kw
        self.events = []

    def __enter__(self):
        self.start = time()
        if getattr(context, 'kw', None):
            raise ValueError("There is already a context defined")

        context.events = self.events
        context.kw = self.kw
        log.debug("%s: entering new context" % (
            threading.current_thread().name,))

        return self.kw

    def __exit__(self, exc_type, exc_value, traceback):
        del context.kw
        del context.events

        self.kw.update(dict(
            events=self.events,
            start=self.start,
            duration=time()-self.start))
        log.info(json.dumps(self.kw))

        log.debug("%s: leaving context" % (
            threading.current_thread().name,))

class MetricsContextApp(object):
    """A WSGI App that will setup a metrics context around the entire request.

    The context is set to environ['metrics_context'], in case you want to
    modify it further, such as specifying the user_id or session_id of the
    request. Usually, you can use "Timer" and "event" without referring to the
    metrics context since it is a threadlocal global.

    The keywords set for the context are:

        REMOTE_ADDR: The REMOTE_ADDR of environ, namely the IP address of the
                     HTTP client making the request.

        PATH_INFO:   The PATH_INFO of the environ, namely the path of the
                     request (without the host.)

        QUERY_STRING: The QUERY_STRING of the environ, namely the GET
                      arguments to the request. This may or may not be useful.

        thread:       The current thread name.
    """
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

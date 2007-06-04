# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - event (notification) framework

    This code abstracts event handling in MoinMoin,
    currently for notifications. It implements the observer pattern.

    @copyright: 2007 by Karol Nowak <grywacz@gmail.com>
    @license: GNU GPL, see COPYING for details.
"""

from MoinMoin import wikiutil
from MoinMoin.util import pysupport
from MoinMoin.wikiutil import PluginAttributeError


# A list of available event handlers
event_handlers = None

# Create a list of extension actions from the package directory
modules = pysupport.getPackageModules(__file__)


class Event:
    """A class handling information common to all events."""
    def __init__(self, request):
        self.request = request

        
class PageEvent(Event):
    """An event related to a page change"""
    def __init__(self, request):
        Event.__init__(self, request)

        
class PageChangedEvent(PageEvent):
    def __init__(self, request, page, comment, trivial):
        PageEvent.__init__(self, request)
        self.page = page
        self.comment = comment
        self.trivial = trivial

        
class PageRenamedEvent(PageEvent):
    pass
class PageDeletedEvent(PageEvent):
    pass
class FileAttachedEvent(PageEvent):
    pass


class PageRevertedEvent(PageEvent):
    def __init__(self, request, pagename, previous, current):
        PageEvent.__init__(self, request)
        self.pagename = pagename
        self.previous = previous
        self.current = current    


class SubscribedToPageEvent(PageEvent):
    def __init__(self, request, pagename, username):
        PageEvent.__init__(self, request)    
        self.pagename = pagename
        self.username = username


class JabberIDSetEvent(Event):
    """ Sent when user changes her Jabber ID """
    def __init__(self, request, jid):
        Event.__init__(self, request)
        self.jid = jid
        

def register_handlers(cfg):
    """Create a list of available event handlers.
    
    Each handler is a handle() function defined in an plugin,
    pretty much like in case of actions.
    
    TODO: maybe make it less dumb? ;-)"""
    
    global event_handlers

    event_handlers = []
    names = wikiutil.getPlugins("events", cfg)

    for name in names:
        try:
            handler = wikiutil.importPlugin(cfg, "events", name, "handle")
        except PluginAttributeError:
            handler = None
        
        if handler is not None:
            event_handlers.append(handler)


def send_event(event):
    """Function called from outside to process an event"""
   
    # A list of messages generated by event handlers, passed back to caller
    msg = []
    
    # Find all available event handlers
    if event_handlers is None:
        register_handlers(event.request.cfg)
    
    # Try to handle the event with each available handler (for now)
    for handle in event_handlers:
        retval = handle(event)
        if isinstance(retval, unicode):
            msg.append(retval)
            
    return msg

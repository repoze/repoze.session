from zope.component import getGlobalSiteManager
from repoze.session.interfaces import ISessionBeginEvent
from repoze.session.interfaces import ISessionEndEvent

sm = getGlobalSiteManager()

def test_event(event):
    print event.__class__, event.session

sm.registerHandler(test_event, (ISessionBeginEvent,))
sm.registerHandler(test_event, (ISessionEndEvent,))

# when a session ends or begins, it will be printed


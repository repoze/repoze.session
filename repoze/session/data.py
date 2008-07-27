import pprint
import time

from zope.interface import implements
from ZODB.POSException import ConflictError

from persistent.mapping import PersistentMapping
from repoze.session.interfaces import ISessionData

def manage_modified(wrapped):
    """ Decorator which sets last modified time on session data
    when a wrapped method is called """

    def set_modified(self, *arg, **kw):
        self.last_modified = time.time()
        return wrapped(self, *arg, **kw)
    return set_modified

class SessionData(PersistentMapping):
    """ Dictionary-like object that supports additional methods and
    attributes concerning invalidation. expiration and conflict
    resolution."""
    implements(ISessionData)

    # Note that we use short instance variable names here to reduce
    # instance pickle sizes, as these items are written quite often to
    # the database under typical usage and it's a material win to do
    # so.

    # _lm (last modified) indicates the last time that __setitem__,
    # __delitem__, update, clear, setdefault, pop, or popitem was
    # called on us.
    _lm = None
    
    # _iv indicates that this node is invalid if true.
    _iv = False

    def __init__(self, d=None):
        # _ct is creation time
        self._ct = time.time()
        PersistentMapping.__init__(self, d)

    # IMapping methods (overridden to manage modification time)

    clear = manage_modified(PersistentMapping.clear)
    update = manage_modified(PersistentMapping.update)
    setdefault = manage_modified(PersistentMapping.setdefault)
    pop = manage_modified(PersistentMapping.pop)
    popitem = manage_modified(PersistentMapping.popitem)
    __setitem__ = manage_modified(PersistentMapping.__setitem__)
    __delitem__ = manage_modified(PersistentMapping.__delitem__)

    # "Smarter" copy (part of IMapping interface)

    def copy(self):
        c = self.__class__(self.data)
        if self._iv:
            c._iv = self._iv
        c._ct = self._ct
        c._lm = self._lm
        return c

    # ISessionData

    def invalidate(self):
        """
        Invalidate (expire) the session data object.
        """
        self._iv = True

    def is_valid(self):
        """
        Return true if session data object is still valid, false if not.
        A session data object is valid if its invalidate method has not been
        called.
        """
        return not self._iv

    def _get_last_modified(self):
        return self._lm

    def _set_last_modified(self, when=None): # 'when' is for testing
        if when is None:
            when = time.time()
        self._lm = when

    last_modified = property(_get_last_modified, _set_last_modified)

    def _get_created(self):
        return self._ct

    created = property(_get_created)

    # ZODB conflict resolution (to prevent write conflicts)

    def _p_resolveConflict(self, old, committed, new):
        # dict modifiers set '_lm'.
        if committed['_lm'] != new['_lm']:
            # we are operating against the PersistentMapping.__getstate__
            # representation, which aliases '_container' to self.data.
            if committed['_container'] != new['_container']:
                msg = "Competing writes to session data: \n%s\n----\n%s" % (
                        pprint.pformat(committed['_container']),
                        pprint.pformat(new['_container']))
                raise ConflictError(msg)

        resolved = dict(new)
        invalid = committed.get('_iv') or new.get('_iv')
        if invalid:
            resolved['_iv'] = True
        resolved['_lm'] = max(committed['_lm'], new['_lm'])
        return resolved

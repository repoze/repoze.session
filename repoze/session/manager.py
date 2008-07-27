import operator
import time

from BTrees.OOBTree import OOBTree
from persistent import Persistent
import transaction
from ZODB.POSException import ConflictError

from zope.interface import implements
from zope.event import notify

from repoze.session.interfaces import ISessionBeginEvent
from repoze.session.interfaces import ISessionEndEvent
from repoze.session.interfaces import ISessionDataManager

from repoze.session.linkedlist import deserialize
from repoze.session.linkedlist import ListNode

from repoze.session.data import SessionData


class SessionBeginEvent(object):
    """ An event that is sent via ``zope.event.notify`` when a session begins.
    """
    implements(ISessionBeginEvent)
    def __init__(self, session):
        self.session = session

class SessionEndEvent(object):
    """ An event that is sent via ``zope.event.notify`` when a session ends.
    """
    implements(ISessionEndEvent)
    def __init__(self, session):
        self.session = session

_marker = ()

class SessionDataManager(Persistent):
    """ An object that manages sessions.
    """
    implements(ISessionDataManager)

    # We have the option of using an OOBTree as a bucket type or an
    # AppendOnlyDict as a bucket type.  With an AppendDict in place,
    # zero conflicts are generated when bucket nodes are mutated
    # because we can resolve all conflicts.  With an OOBTree in place,
    # some conflicts are generated due to interior node splits.  But
    # empirical testing shows that using an OOBTree makes session
    # access faster and produces much smaller pickles, even if its
    # usage does imply tolerating some conflicts.
        
    _BUCKET_TYPE = OOBTree

    # Make the data type replaceable for unit tests.
    _DATA_TYPE = SessionData

    nonlazy = False # for unit testing

    def __init__(self, timeout, period, when=None):
        self.timeout = timeout # seconds
        self.period = period   # seconds
        self.head = self.new_head(None, when)

    #   ISessionDataManager implementation

    def get(self, key, when=None):  # 'when' for testing
        """
        If an object already exists in the manager with key "k", it
        is returned.

        Otherwise, create a new subobject of the type supported by this
        container with key "k" and return it.
        """
        sdo = self.search(key, when=when)

        if sdo is None or not sdo.is_valid():
            sdo = self._DATA_TYPE()
            # It is useful to only need to persist the data object
            # into the head bucket iff it was actually modified during
            # the transaction.  This potentially cuts down on the
            # number of writes to the database by an order of
            # magnitude in the case where someone unleashes "ab" or a
            # similar tool against a page which accesses a session but
            # does not write to it (such as a login form that uses
            # session auth or a shopping cart page).  If we are
            # 'lazy', we only set the new session data object into the
            # head bucket if it has been modified during the
            # transaction.  We use a ZODB 'beforeCommitHook' to
            # perform this conditional.  If self.nonlazy is true, we
            # don't use this behavior, but this is typically only
            # useful for unit tests.
            t = transaction.get()
            if self.nonlazy:
                self.set(key, sdo, when)
            else:
                t.addBeforeCommitHook(self.set_if_modified, (key, sdo, when))

            notify(SessionBeginEvent(sdo))

        return sdo

    def query(self, key, default=None):
        """
        Return value associated with key k.  If value associated with
        k does not exist, return default.
        """
        return self.search(key, default)

    def has_key(self, key):
        """
        Return true if manager has value associated with key k, else
        return false.
        """
        return self.search(key, None) is not None

    #
    # Linked list management
    #
    def new_head(self, old_head, when=None):
        if when is None:
            when = time.time()

        bucket = self._BUCKET_TYPE()
        head = ListNode((when, bucket), old_head)
        return head

    def get_head(self, when=None):
        if when is None:
            when = time.time()

        now_slice = timeslice(self.period, when)

        # head_slice is the slice in which the head bucket was created
        head_slice, head_bucket = self.head.ob

        # if the now timeslice is equal to or before the head was
        # created, we do not need to replace the head, as it is still
        # current.

        if now_slice > head_slice:
            # the head is not current, we need to replace it
            self.head = self.new_head(self.head, now_slice)

        return self.head

    def search(self, k, default=None, when=None):   # 'when' for testing
        head = self.get_head(when)

        head_slice, head_bucket = head.ob
        node = head

        current_buckets = []

        while node is not None:

            ignored, bucket = node.ob
            current_buckets.append(bucket)

            value = bucket.get(k, _marker)

            if value is not _marker:
                if node is not head:
                    head_bucket[k] = value
                return value

            nextnode = node.next

            if nextnode is not None:

                next_slice, next_bucket = nextnode.ob

                if head_slice - next_slice > self.timeout:
                    self.notify_end(nextnode, current_buckets)
                    node.next = None

            node = node.next

        return default

    def notify_end(self, expired_node, current_buckets):
        # finalize all values that don't have a key that is current

        # flatten all keys in current buckets
        current_keys = {}
        for current_bucket in current_buckets:
            for k in current_bucket.keys():
                current_keys[k] = 1

        while expired_node is not None:
            ignored, bucket = expired_node.ob
            for k, v in bucket.items():
                if k in current_keys:
                    continue
                event = SessionEndEvent(v)
                notify(event)
                # don't finalize data objects with the same key twice
                current_keys[k] = v

            expired_node = expired_node.next
            
    def set(self, k, v, when=None):
        head = self.get_head(when)
        head_ts, bucket = head.ob
        bucket[k] = v

    def set_if_modified(self, k, v, when=None):
        if v.last_modified is not None:
            self.set(k, v, when)

    # Conflict resolution

    def _p_resolveConflict(self, old, committed, new):
        oldob       = State(old)
        committedob = State(committed)
        newob       = State(new)
        
        if not oldob.period == committedob.period == newob.period:
            raise ConflictError('Conflicting periods')

        if not oldob.timeout == committedob.timeout == newob.timeout:
            raise ConflictError('Conflicting timeouts')

        o_head, o_tail = _head_and_tail(oldob)
        c_head, c_tail = _head_and_tail(committedob)
        n_head, n_tail = _head_and_tail(newob)

        # We are operating on the __setstate__ representation of the
        # attached ListNodes (no clue why, we're operating on the
        # __getstate__ representation of the PersistentMapping object
        # in SessionDataObject).
        o_head_ts = o_head.ob[0]
        if o_head_ts < c_tail.ob[0]:
            raise ConflictError('Committed has obsoleted old')

        if o_head_ts < n_tail.ob[0]:
            raise ConflictError('New has obsoleted old')

        # find any slices added in 'new'
        n_added = _prefix(n_head, o_head_ts)

        # and portion of 'committed' newer than new's tail.
        c_rest = _prefix(c_head, n_tail.ob[0], include_match=True)

        head = deserialize(n_added + c_rest)
        new['head'] = head
        return new

def _prefix(newer, ts, include_match=False):
    result = []
    op = include_match and operator.ge or operator.gt
    while newer and op(newer.ob[0], ts):
        result.append(newer.ob)
        newer = newer.next
    return result
    
def _head_and_tail(root):
    head = tail = root.head
    while tail and tail.next is not None:
        tail = tail.next
    return head, tail

class State:
    # make dealing with conflict resolution a bit easier
    def __init__(self, d):
        self.__dict__.update(d)

def timeslice(period, when=None):
    if when is None:
        when =  time.time()
    return when - (when % period)

class SessionManagerFactory(object):
    def __call__(self, connection_handler=None):
        conn = self.db.open()
        if connection_handler:
            connection_handler(conn)
        root = conn.root()
        if root.get(self.appname) is None:
            root[self.appname] = SessionDataManager(self.timeout, self.period)
        return root[self.appname]

class FileStorageSessionManagerFactory(SessionManagerFactory):
    """ Create a factory that is, in turn, capable of creating a
    session manager.  The session manager is stored in a ZODB
    FileStorage.  ``filename`` is he ZODB filestorage filename,
    ``appname`` is the name in the ZODB under which the session
    manager will be stored.  ``timeout`` is the session manager
    :term:`timeout`, and ``period`` is the session manager
    :term:`period`"""
    def __init__(self, filename, appname, timeout=1200, period=20):
        from ZODB.FileStorage.FileStorage import FileStorage
        from ZODB.DB import DB
        f = FileStorage(filename)
        self.db = DB(f)
        self.appname = appname
        self.timeout = timeout
        self.period = period

    def __del__(self):
        self.db.close()
        
class ConnectionManager(object):
    """ An object willing to manage a ZODB database connection """
    def __call__(self, conn):
        """ Store the connection. """
        self.conn = conn

    def close(self):
        """ Close the connection. """
        self.conn.close()

    def __del__(self):
        self.close()

    def commit(self, transaction=transaction):
        """ Commit a transaction. """
        transaction.commit()


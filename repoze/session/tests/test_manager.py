import unittest

from zope.component.testing import PlacelessSetup

class SessionDataManagerTests(unittest.TestCase, PlacelessSetup):
    def setUp(self):
        PlacelessSetup.setUp(self)

    def tearDown(self):
        PlacelessSetup.tearDown(self)

    def _makeOne(self, timeout=60, period=5, when=None):
        klass = self._getTargetClass()
        return klass(timeout, period, when)

    def _getTargetClass(self):
        from repoze.session.manager import SessionDataManager
        return SessionDataManager

    def test_class_conforms_to_ISessionDataManager(self):
        from zope.interface.verify import verifyClass
        from repoze.session.interfaces import ISessionDataManager
        verifyClass(ISessionDataManager, self._getTargetClass())

    def test_inst_conforms_to_ISessionDataManager(self):
        from zope.interface.verify import verifyObject
        from repoze.session.interfaces import ISessionDataManager
        inst = self._makeOne()
        verifyObject(ISessionDataManager, inst)

    def test_set_get_and_has_key(self):
        sdc = self._makeOne()
        self.assertEqual(sdc.has_key('foo'), False)
        self.assertEqual(sdc.query('foo'), None)
        sdc.set('foo', 'bar')
        self.assertEqual(sdc.has_key('foo'), True)
        self.assertEqual(sdc.query('foo'), 'bar')

    def test_get(self):
        from repoze.session.interfaces import ISessionData
        sdc = self._makeOne()
        sdo = sdc.get('a')
        self.failUnless(ISessionData.providedBy(sdo))

    def test___init__(self):
        root = self._makeOne(30, 1)
        head = root.head
        self.assertEqual(root.timeout, 30)
        self.assertEqual(root.period, 1)
        self.assertEqual(head.next, None)
        self.failUnless(isinstance(head.ob[0], float))
        self.failUnless(isinstance(head.ob[1], root._BUCKET_TYPE))

    def test_new_head(self):
        from repoze.session.linkedlist import ListNode
        root = self._makeOne(30, 1)
        newhead = root.new_head('abc')
        self.failUnless(isinstance(newhead, ListNode))
        self.assertEqual(newhead.next, 'abc')
        self.failUnless(isinstance(newhead.ob[0], float))
        self.failUnless(isinstance(newhead.ob[1], root._BUCKET_TYPE))

    def test_get_head_noreplace(self):
        from repoze.session.linkedlist import ListNode
        root = self._makeOne(30, 1)
        head = root.get_head()
        ts, bucket = head.ob
        self.failUnless(isinstance(head, ListNode))
        self.failUnless(isinstance(bucket, root._BUCKET_TYPE))
        self.failUnless(isinstance(ts, float))
        self.assertEqual(head.next, None)

    def test_get_head_successive_timeslices(self):

        # we begin the root with a timeout of 30, a period of 1, and a
        # "when" of 1, which implies that the head is "valid until"
        # the timeslice numbered 1
        root = self._makeOne(30, 1, when=1)

        # if we ask for the head during timeslice "1", we should not cause the
        # head to be bumped (becase the head bucket is valid until 1)
        head = root.get_head(when=1)
        self.assertEqual(len(head), 1)

        # if we go back in time to timeslice 0, same thing.
        head = root.get_head(when=0)
        self.assertEqual(len(head), 1)

        # the head is valid until 1, so when we ask for 1, we still don't bump
        # the head even after asking for 0
        head = root.get_head(when=1)
        self.assertEqual(len(head), 1)

        # if we bump up the timeslice to 2, the length of the linked list
        # should become two, because the head bucket will have become
        # invalid and another will have been added (the one that is
        # 'valid until 3').
        head = root.get_head(when=2)
        self.assertEqual(len(head), 2)
        self.assertEqual(head.ob[0], 2)

        # and again
        head = root.get_head(when=3)
        self.assertEqual(len(head), 3)
        self.assertEqual(head.ob[0], 3)

        # and again
        head = root.get_head(when=4)
        self.assertEqual(len(head), 4)
        self.assertEqual(head.ob[0], 4)

        # but fractions don't bump the head
        head = root.get_head(when=4.1)
        self.assertEqual(len(head), 4)

        head = root.get_head(when=4.999)
        self.assertEqual(len(head), 4)

        # but rollovers to the next whole timeslice do
        head = root.get_head(when=5)
        self.assertEqual(len(head), 5)

        # we can skip timeslices
        head = root.get_head(when=10)
        self.assertEqual(len(head), 6)

        head = root.get_head(when=10)
        self.assertEqual(len(head), 6)

        head = root.get_head(when=7)
        self.assertEqual(len(head), 6)

        # and again
        head = root.get_head(when=11)
        self.assertEqual(len(head), 7)

        head = root.get_head(when=10)
        self.assertEqual(len(head), 7)

    def test_get_head_replace(self):
        import time
        now = time.time()
        root = self._makeOne(30, 1)
        originalhead = root.head
        head = root.get_head(now + 86400) # new timeslice will be 1 day from now
        self.assertNotEqual(originalhead, head)
        self.assertEqual(head.next, originalhead)

    def test_search_findinhead(self):
        root = self._makeOne(30, 1)
        bucket = root.head.ob[1]
        bucket['a'] = 1
        self.assertEqual(root.search('a'), 1)

    def test_search_findintail(self):
        root = self._makeOne(30, 1)
        root.head.ob[1]['a'] = 1

        from repoze.session.linkedlist import ListNode
        import time

        newbucket = root._BUCKET_TYPE()
        now = time.time()
        newhead = ListNode((now, newbucket), root.head)
        root.head = newhead
        self.assertEqual(root.search('a'), 1)

        # value was moved forward
        self.assertEqual(newbucket.get('a'), 1)

    def test_search_newer_shadows_older(self):
        root = self._makeOne(30, 1)
        root.head.ob[1]['a'] = 1

        from repoze.session.linkedlist import ListNode
        import time

        newbucket = root._BUCKET_TYPE()
        newbucket['a'] = 2
        now = time.time()
        newhead = ListNode((now, newbucket), root.head)
        root.head = newhead
        self.assertEqual(root.search('a'), 2)

    def test_set(self):
        root = self._makeOne(30, 1)
        root.set('a', 1)
        self.assertEqual(root.head.ob[1]['a'], 1)

    # Tres' tests
    def test_CR_period_conflict_raises_ConflictError(self):
        from ZODB.POSException import ConflictError
        old = self._makeOne(30, 1)
        committed = self._makeOne(30, 3)
        new = self._makeOne(30, 2)

        self.assertRaises(ConflictError,
                          new._p_resolveConflict,
                          *_statify(old, committed, new))

    def test_CR_timeout_conflict_raises_ConflictError(self):
        from ZODB.POSException import ConflictError
        old = self._makeOne(30, 1)
        committed = self._makeOne(32, 1)
        new = self._makeOne(31, 1)

        self.assertRaises(ConflictError,
                          new._p_resolveConflict,
                          *_statify(old, committed, new))

    def test_CR_committed_tail_newer_than_old_head_raises_ConflictError(self):
        from ZODB.POSException import ConflictError
        from repoze.session.linkedlist import ListNode

        old = self._makeOne(30, 1)
        old.head = ListNode((1234, {}), None)

        # The tail of 'committed' is more recent than the head of 'old',
        # which makes any attempt at conflict resolution pointless.
        committed = self._makeOne(30, 1)
        committed.head = ListNode((2345, {}), None)

        new = self._makeOne(30, 1)
        new.head = ListNode((3456, {}), None)

        self.assertRaises(ConflictError,
                          new._p_resolveConflict,
                          *_statify(old, committed, new))

    def test_CR_new_tail_newer_than_old_head_raises_ConflictError(self):
        from ZODB.POSException import ConflictError
        from repoze.session.linkedlist import ListNode

        old = self._makeOne(30, 1)
        o_h = old.head = ListNode((1234, {}), None)

        committed = self._makeOne(30, 1)
        committed.head = ListNode((2345, {}), o_h)

        # The tail of 'new' is more recent than the head of 'old',
        # which makes any attempt at conflict resolution pointless.
        new = self._makeOne(30, 1)
        new.head = ListNode((3456, {}), None)

        self.assertRaises(ConflictError,
                          new._p_resolveConflict,
                          *_statify(old, committed, new))

    def test_CR_both_adding(self):
        from repoze.session.linkedlist import ListNode

        old = self._makeOne(30, 1)
        oh = old.head = ListNode((1234, {}), ListNode((1000, {}), None))

        committed = self._makeOne(30, 1)
        committed.head = ListNode((2345, {}), oh)

        new = self._makeOne(30, 1)
        new.head = ListNode((3456, {}), oh)

        resolved = new._p_resolveConflict(*_statify(old, committed, new))

        nodes = _flatten(resolved['head'])
        self.assertEqual(len(nodes), 4)
        self.assertEqual([x[0] for x in nodes], [3456, 2345, 1234, 1000])

    def test_CR_both_truncating(self):
        from repoze.session.linkedlist import ListNode

        old = self._makeOne(30, 1)
        oh = old.head = ListNode((1234, {}), ListNode((1000, {}), None))

        committed = self._makeOne(30, 1)
        committed.head = ListNode((1234, {}), None)

        new = self._makeOne(30, 1)
        new.head = ListNode((1234, {}), None)

        resolved = new._p_resolveConflict(*_statify(old, committed, new))

        nodes = _flatten(resolved['head'])
        self.assertEqual(len(nodes), 1)
        self.assertEqual([x[0] for x in nodes], [1234])

    def test_CR_committed_adding_new_truncating(self):
        from repoze.session.linkedlist import ListNode

        old = self._makeOne(30, 1)
        oh = old.head = ListNode((1234, {}), ListNode((1000, {}), None))

        committed = self._makeOne(30, 1)
        committed.head = ListNode((2345, {}), oh)

        new = self._makeOne(30, 1)
        new.head = ListNode((1234, {}), None) # truncating only

        resolved = new._p_resolveConflict(*_statify(old, committed, new))

        nodes = _flatten(resolved['head'])
        self.assertEqual(len(nodes), 2)
        self.assertEqual([x[0] for x in nodes], [2345, 1234])

    def test_CR_committed_truncating_new_adding(self):
        from repoze.session.linkedlist import ListNode

        old = self._makeOne(30, 1)
        oh = old.head = ListNode((1234, {}), ListNode((1000, {}), None))

        committed = self._makeOne(30, 1)
        committed.head = ListNode((1234, {}), None) # truncating only

        new = self._makeOne(30, 1)
        new.head = ListNode((2345, {}), oh)

        resolved = new._p_resolveConflict(*_statify(old, committed, new))

        nodes = _flatten(resolved['head'])
        self.assertEqual(len(nodes), 2)
        self.assertEqual([x[0] for x in nodes], [2345, 1234])

    def test_CR_both_adding_committed_truncating(self):
        from repoze.session.linkedlist import ListNode

        old = self._makeOne(30, 1)
        oh = old.head = ListNode((1234, {}), ListNode((1000, {}), None))

        committed = self._makeOne(30, 1)
        committed.head = ListNode((2345, {}), ListNode((1234, {}), None))

        new = self._makeOne(30, 1)
        new.head = ListNode((3456, {}), oh)

        resolved = new._p_resolveConflict(*_statify(old, committed, new))

        nodes = _flatten(resolved['head'])
        self.assertEqual(len(nodes), 3)
        self.assertEqual([x[0] for x in nodes], [3456, 2345, 1234])

    def test_CR_both_adding_new_truncating(self):
        from repoze.session.linkedlist import ListNode

        old = self._makeOne(30, 1)
        oh = old.head = ListNode((1234, {}), ListNode((1000, {}), None))

        committed = self._makeOne(30, 1)
        committed.head = ListNode((2345, {}), oh)

        new = self._makeOne(30, 1)
        new.head = ListNode((3456, {}), ListNode((1234, {}), None))

        resolved = new._p_resolveConflict(*_statify(old, committed, new))

        nodes = _flatten(resolved['head'])
        self.assertEqual(len(nodes), 3)
        self.assertEqual([x[0] for x in nodes], [3456, 2345, 1234])


    # Chris' tests
    def _makeState(self, timeout, period, head):
        return {'timeout':timeout, 'period':period, 'head':head}

    def test__p_resolveConflict_differingperiods(self):
        root = self._makeOne(30, 1)
        old       = self._makeState(1, 1, None)
        committed = self._makeState(1, 2, None)
        new       = self._makeState(1, 2, None)
        from ZODB.POSException import ConflictError
        self.assertRaises(ConflictError, root._p_resolveConflict,
                          old, committed, new)

    def test__p_resolveConflict_differingtimeouts(self):
        root = self._makeOne(30, 1)
        old       = self._makeState(1, 1, None)
        committed = self._makeState(2, 1, None)
        new       = self._makeState(2, 1, None)
        from ZODB.POSException import ConflictError
        self.assertRaises(ConflictError, root._p_resolveConflict,
                          old, committed, new)

    def test__p_resolveConflict_nointersection(self):
        from repoze.session.linkedlist import ListNode
        from ZODB.POSException import ConflictError
        root = self._makeOne(30, 1)
        old       = self._makeState(1, 1, ListNode((1, {}),None))
        committed = self._makeState(1, 1, ListNode((2, {}),None))
        new       = self._makeState(1, 1, ListNode((3, {}),None))
        self.assertRaises(ConflictError, root._p_resolveConflict,
                          old, committed, new)

    def test__p_resolveConflict_both_committed_and_new_have_new_head(self):
        from repoze.session.linkedlist import ListNode
        root = self._makeOne(30, 1)
        shared_node_tail = ListNode((1, {}), None)
        shared_node_head = ListNode((2, {}), shared_node_tail)
        old       = self._makeState(1, 1, shared_node_head)
        committed = self._makeState(1, 1, ListNode((3, {}), shared_node_head))
        new       = self._makeState(1, 1, ListNode((4, {}), shared_node_head))
        result = root._p_resolveConflict(old, committed, new)
        # note that we've composed the linked list out of both the
        # shared elements and the new head elements in committed and
        # new
        self.assertEqual(result['period'], 1)
        self.assertEqual(result['timeout'], 1)
        head = result['head']
        self.assertEqual(head.ob[0], 4)
        next = head.next
        self.assertEqual(next.ob[0], 3)
        next = next.next
        self.assertEqual(next.ob[0], 2)
        next = next.next
        self.assertEqual(next.ob[0], 1)
        next = next.next
        self.assertEqual(next, None)

    def test__p_resolveConflict_differing_tails(self):
        from repoze.session.linkedlist import ListNode
        root = self._makeOne(30, 1)

        long_tail     = ListNode((1, {}), None)
        long_between  = ListNode((2, {}), long_tail)
        long_head     = ListNode((3, {}), long_between)

        mid_tail      = ListNode((2, {}), None)
        mid_head      = ListNode((3, {}), mid_tail)

        short_head    = ListNode((3, {}), None)

        old       = self._makeState(1, 1, long_head)
        committed = self._makeState(1, 1, mid_head)
        new       = self._makeState(1, 1, short_head)

        result = root._p_resolveConflict(old, committed, new)
        self.assertEqual(result['period'], 1)
        self.assertEqual(result['timeout'], 1)
        # we take the intersection of the three states, so we only get "3" back
        head = result['head']
        self.assertEqual(head.ob[0], 3)
        next = head.next
        self.assertEqual(next, None)

    def test_set_if_modified(self):
        root = self._makeOne(30, 1)
        sdo = root.get('a')
        root.set_if_modified('a', sdo)
        self.failIf(sdo is root.get('a'))
        sdo['foo'] = 'bar'
        root.set_if_modified('a', sdo)
        self.failIf(sdo is not root.get('a'))

    def test_laziness(self):
        import transaction
        root = self._makeOne(30, 1)
        sdo = root.get('a')
        t = transaction.get()
        hooks = list(t.getBeforeCommitHooks())
        self.failUnless(hooks)
        for hook in hooks:
            self.assertEqual(hook[0].im_func.func_code,
                             root.set_if_modified.im_func.func_code)
            self.assertEqual(hook[1], ('a', sdo, None)) # *arg
            self.assertEqual(hook[2], {})   # **kw

        t.abort() # clear commit hooks

    def test_begin_notifier(self):
        import zope.component
        gsm = zope.component.getGlobalSiteManager()
        from repoze.session.interfaces import ISessionBeginEvent
        stuff = []
        def test_event(event):
            stuff.append(event.session)
        gsm.registerHandler(test_event, (ISessionBeginEvent,))
        sdc = self._makeOne(30, 1)
        sdc.nonlazy = True
        sdo = sdc.get('a')
        self.assertEqual(len(stuff), 1)
        self.assertEqual(stuff[0], sdo)

    def test_end_notifier(self):
        import zope.component
        gsm = zope.component.getGlobalSiteManager()
        from repoze.session.interfaces import ISessionEndEvent
        stuff = []
        def test_event(event):
            stuff.append(event.session)

        gsm.registerHandler(test_event, (ISessionEndEvent,))
        sdc = self._makeOne(30, 1, when=1)
        sdc.nonlazy = True

        a = sdc.get('a', when=1)

        # 'a' should get finalized when its timeout is reached; we
        # cause a timeout by adding a 'b' in timeslice 60
        b = sdc.get('b', when=60)
        self.assertEqual(len(stuff), 1)
        self.assertEqual(stuff[0], a)

        # 'b' should get finalized when its timeout is reached; we
        # cause a timeout by adding a 'c' in timeslice 600
        c = sdc.get('c', when=600)
        self.assertEqual(len(stuff), 2)
        self.assertEqual(stuff[1], b)

        # 'c' should not finalized when the timeout is reached again
        new_c = sdc.get('c', when=600)
        self.failUnless(c is new_c)
        self.assertEqual(len(stuff), 2)

        # 'c' should not finalized when the timeslice doesn't change
        new_c_2 = sdc.get('c', when=629)
        self.failUnless(new_c_2 is new_c)
        self.assertEqual(len(stuff), 2)

        # 'c' should get finalized when the timeout is reached again,
        # even if we ask for it during the new timeslice by name.
        new_c_3 = sdc.get('c', when=1200)
        self.failIf(new_c_3 is new_c_2)
        self.assertEqual(len(stuff), 3)
        self.assertEqual(stuff[2], c)


    def test_notify_end_with_current_buckets(self):
        sdc = self._makeOne(30, 1, when=1)
        sdc.notify_end(None, current_buckets=[{'a':1}, {'b':2}])
        

class TestFileStorageSessionManagerFactory(unittest.TestCase):
    def _getTargetClass(self):
        from repoze.session.manager import FileStorageSessionManagerFactory
        return FileStorageSessionManagerFactory

    def _makeOne(self, filename, appname):
        klass = self._getTargetClass()
        return klass(filename, appname)

    def setUp(self):
        import tempfile
        self.tempfile = tempfile.mktemp()

    def tearDown(self):
        import os
        os.remove(self.tempfile)

    def test_no_conn_handler(self):
        factory = self._makeOne(self.tempfile, 'session')
        from repoze.session.manager import SessionDataManager
        catalog = factory()
        self.failUnless(isinstance(catalog, SessionDataManager))
        factory.db.close()

    def test_with_conn_handler(self):
        factory = self._makeOne(self.tempfile, 'session')
        from repoze.session.manager import SessionDataManager
        e = {}
        def handle(conn):
            e['conn'] = conn
        catalog = factory(handle)
        self.failUnless(isinstance(catalog, SessionDataManager))
        self.assertEqual(e['conn']._db, factory.db)
        factory.db.close()

class TestConnectioManager(unittest.TestCase):
    def _getTargetClass(self):
        from repoze.session.manager import ConnectionManager
        return ConnectionManager

    def _makeOne(self):
        klass = self._getTargetClass()
        return klass()

    def test_call(self):
        conn = DummyConnection()
        manager = self._makeOne()
        manager(conn)
        self.assertEqual(manager.conn, conn)
        
    def test_close(self):
        conn = DummyConnection()
        manager = self._makeOne()
        manager(conn)
        manager.close()
        self.assertEqual(conn.closed, True)

    def test_del(self):
        conn = DummyConnection()
        manager = self._makeOne()
        manager(conn)
        del manager
        self.assertEqual(conn.closed, True)

    def test_commit(self):
        conn = DummyConnection()
        txn = DummyTransaction()
        manager = self._makeOne()
        manager(conn)
        manager.commit(txn)
        self.assertEqual(txn.committed, True)

class TestTimeslice(unittest.TestCase):
    def _callFUT(self, period, when=None):
        from repoze.session.manager import timeslice
        return timeslice(period, when)

    def test_it_when_None(self):
        result = self._callFUT(60)
        self.assertEqual(type(result), float)

    def test_it_when_supplied(self):
        result = self._callFUT(60, 600)
        self.assertEqual(result, 600)

class DummyConnection:
    def close(self):
        self.closed = True

class DummyTransaction:
    def commit(self):
        self.committed = True

def _statify(*things):
    return [{'timeout':x.timeout, 'period':x.period, 'head':x.head}
                for x in things]

def _flatten(head):
    result = []
    while head is not None:
        result.append(head.ob)
        head = head.next
    return result

            

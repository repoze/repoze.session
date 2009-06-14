import unittest

class TestSessionData(unittest.TestCase):
    def _getTargetClass(self):
        from repoze.session.data import SessionData
        return SessionData

    def _makeOne(self, data=None):
        return self._getTargetClass()(data)

    def test_instance_implements_ISessionData(self):
        from zope.interface.verify import verifyObject
        from repoze.session.interfaces import ISessionData
        verifyObject(ISessionData, self._makeOne())

    def test_class_implements_ISessionData(self):
        from zope.interface.verify import verifyClass
        from repoze.session.interfaces import ISessionData
        verifyClass(ISessionData, self._getTargetClass())

    def test_mapping_interface(self):
        SessionDataObject = self._getTargetClass()

        # this test body mostly stolen from persistent.tests.test_mapping

        # Test constructors
        l0 = {}
        l1 = {0:0}
        l2 = {0:0, 1:1}
        u = SessionDataObject()
        u0 = SessionDataObject(l0)
        u1 = SessionDataObject(l1)
        u2 = SessionDataObject(l2)

        uu = SessionDataObject(u)
        uu0 = SessionDataObject(u0)
        uu1 = SessionDataObject(u1)
        uu2 = SessionDataObject(u2)

        class OtherMapping:
            def __init__(self, initmapping):
                self.__data = initmapping
            def items(self):
                return self.__data.items()
        v0 = SessionDataObject(OtherMapping(u0))
        vv = SessionDataObject([(0, 0), (1, 1)])

        # Test __repr__
        eq = self.assertEqual

        eq(str(u0), str(l0))#, "str(u0) == str(l0)")
        eq(repr(u1), repr(l1), "repr(u1) == repr(l1)")
        eq(`u2`, `l2`, "`u2` == `l2`")

        # Test __cmp__ and __len__

        def mycmp(a, b):
            r = cmp(a, b)
            if r < 0: return -1
            if r > 0: return 1
            return r

        all = [l0, l1, l2, u, u0, u1, u2, uu, uu0, uu1, uu2]
        for a in all:
            for b in all:
                eq(mycmp(a, b), mycmp(len(a), len(b)),
                      "mycmp(a, b) == mycmp(len(a), len(b))")

        # Test __getitem__

        for i in range(len(u2)):
            eq(u2[i], i, "u2[i] == i")

        # Test get

        for i in range(len(u2)):
            eq(u2.get(i), i, "u2.get(i) == i")
            eq(u2.get(i, 5), i, "u2.get(i, 5) == i")

        for i in min(u2)-1, max(u2)+1:
            eq(u2.get(i), None, "u2.get(i) == None")
            eq(u2.get(i, 5), 5, "u2.get(i, 5) == 5")

        # Test __setitem__

        uu2[0] = 0
        uu2[1] = 100
        uu2[2] = 200

        # Test __delitem__

        del uu2[1]
        del uu2[0]
        try:
            del uu2[0]
        except KeyError:
            pass
        else:
            raise ValueError("uu2[0] shouldn't be deletable")

        # Test __contains__
        for i in u2:
            self.failUnless(i in u2, "i in u2")
        for i in min(u2)-1, max(u2)+1:
            self.failUnless(i not in u2, "i not in u2")

        # Test update

        l = {"a":"b"}
        u = SessionDataObject(l)
        u.update(u2)
        for i in u:
            self.failUnless(i in l or i in u2, "i in l or i in u2")
        for i in l:
            self.failUnless(i in u, "i in u")
        for i in u2:
            self.failUnless(i in u, "i in u")

        # Test setdefault

        x = u2.setdefault(0, 5)
        eq(x, 0, "u2.setdefault(0, 5) == 0")

        x = u2.setdefault(5, 5)
        eq(x, 5, "u2.setdefault(5, 5) == 5")
        self.failUnless(5 in u2, "5 in u2")

        # Test pop

        x = u2.pop(1)
        eq(x, 1, "u2.pop(1) == 1")
        self.failUnless(1 not in u2, "1 not in u2")

        try:
            u2.pop(1)
        except KeyError:
            pass
        else:
            raise ValueError("1 should not be poppable from u2")

        x = u2.pop(1, 7)
        eq(x, 7, "u2.pop(1, 7) == 7")

        # Test popitem

        items = u2.items()
        key, value = u2.popitem()
        self.failUnless((key, value) in items, "key, value in items")
        self.failUnless(key not in u2, "key not in u2")

        # Test clear

        u2.clear()
        eq(u2, {}, "u2 == {}")

    def test_invalidate_and_isValid(self):
        sdo = self._makeOne()
        self.assertEqual(sdo.is_valid(), True)
        sdo.invalidate()
        self.assertEqual(sdo.is_valid(), False)

    def test_get_and_set_last_modified(self):
        sdo = self._makeOne()
        self.assertEqual(sdo.last_modified, None)
        when = 100
        sdo.last_modified = when
        self.assertEqual(sdo.last_modified, when)

    def test_set_last_modified_None(self):
        sdo = self._makeOne()
        sdo.last_modified = None
        self.failIf(sdo.last_modified is None)

    def test_created(self):
        sdo = self._makeOne()
        import time
        time.sleep(.05)
        t = time.time()
        self.failIf( sdo.created > t )

    def test_modmethods(self):
        import time
        sdo = self._makeOne()
        modmethods = (
            ('clear',),
            ('update', {'a':1, 'z':5}),
            ('setdefault', 'b', 1),
            ('pop', 'b'),
            ('popitem',),
            ('__setitem__', 'c', '1'),
            ('__delitem__', 'c'),
            )
        modified = 0
        for methargs in modmethods:
            methname = methargs[0]
            args = methargs[1:]
            method = getattr(sdo, methname)
            method(*args)
            newmodified = sdo.last_modified
            self.failUnless( newmodified > modified)
            modified = newmodified
            time.sleep(.02)

    def test_copy(self):
        sdo = self._makeOne()
        sdo._iv = True
        sdo2 = sdo.copy()
        self.assertEqual(sdo.data, sdo2.data)
        self.assertEqual(sdo.is_valid(), sdo2.is_valid())
        self.assertEqual(sdo.created, sdo2.created)
        self.assertEqual(sdo.last_modified, sdo2.last_modified)

    def test_p_resolveConflict_different_lm_different_container(self):
        from ZODB.POSException import ConflictError
        sdo = self._makeOne()
        old = {}
        committed = {'_lm':1, '_container':1}
        new       = {'_lm':2, '_container':2}
        self.assertRaises(ConflictError, sdo._p_resolveConflict, old,
                          committed, new)

    def test_p_resolveConflict_different_lm_same_container(self):
        sdo = self._makeOne()
        old = {}
        committed = {'_lm':1, '_container':1, '_la':1, '_iv':1}
        new       = {'_lm':2, '_container':1, '_la':1, '_iv':1}
        result = sdo._p_resolveConflict(old, committed, new)
        self.assertEqual(
            result,
            {'_la': 1, '_container': 1, '_lm': 2, '_iv': True}
            )

    def test_p_resolveConflict_same_lm(self):
        sdo = self._makeOne()
        old = {}
        committed = {'_lm':1, '_container':1}
        new       = {'_lm':1, '_container':1}
        result = sdo._p_resolveConflict(old, committed, new)
        self.assertEqual(result, {'_container': 1, '_lm': 1})

    

    

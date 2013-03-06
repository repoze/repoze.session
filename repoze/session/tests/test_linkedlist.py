import unittest

class SerializationTests(unittest.TestCase):

    def test_deserialize(self):
        from repoze.session import linkedlist
        testseq = [1, 2, 7, 10, None, unittest]
        node = linkedlist.deserialize(testseq)
        for item in testseq:
            self.assertEqual(node.ob, item)
            node = node.next
        self.assertEqual(node, None)

    def test_serialize(self):
        from repoze.session import linkedlist
        node3 = linkedlist.ListNode(3)
        node2 = linkedlist.ListNode(2, node3)
        node1 = linkedlist.ListNode(1, node2)
        self.assertEqual(linkedlist.serialize(node1), [1,2,3])

    def test_pickle(self):
        from repoze.session._compat import pickle
        from repoze.session import linkedlist
        import string
        node = linkedlist.deserialize(range(26))
        dumped_data = pickle.dumps(linkedlist.serialize(node), 2)
        dumped_node = pickle.dumps(node, 2)

        new_node = pickle.loads(dumped_node)
        self.assertEqual(linkedlist.serialize(new_node),
                         linkedlist.serialize(node))

        # Efficient pickling uses list repr
        self.failUnless(dumped_data[5:-1] in dumped_node)

    def test_repr(self):
        from repoze.session import linkedlist
        testseq = [1]
        node = linkedlist.deserialize(testseq)
        self.failUnless(repr(node).startswith('<ListNode object'))

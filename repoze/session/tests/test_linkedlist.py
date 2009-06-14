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
        import cPickle
        from repoze.session import linkedlist
        import string
        node = linkedlist.deserialize(string.uppercase)
        dumped_data = cPickle.dumps(linkedlist.serialize(node))
        dumped_node = cPickle.dumps(node)

        new_node = cPickle.loads(dumped_node)
        self.assertEqual(linkedlist.serialize(new_node),
                         linkedlist.serialize(node))

        # Efficient pickling uses list repr
        self.failUnless(dumped_data[4:-1] in dumped_node)

    def test_repr(self):
        from repoze.session import linkedlist
        testseq = [1]
        node = linkedlist.deserialize(testseq)
        self.failUnless(repr(node).startswith('<ListNode object'))
        

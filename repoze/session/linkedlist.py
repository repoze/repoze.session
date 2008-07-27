class ListNode(object):
    __slots__ = ('ob', 'next')

    def __getstate__(self):
        return serialize(self)

    def __setstate__(self, value):
        node = deserialize(value)
        self.ob, self.next = node.ob, node.next

    def __init__(self, ob, next=None):
        self.ob = ob
        self.next = next

    def __len__(self):
        return len(serialize(self))

    def __nonzero__(self):
        # don't call __len__ on "if listnode:"
        return True

    def __repr__(self):
        return '<ListNode object at %s for ob %r with next %r>' % (
            id(self), self.ob, self.next)

def serialize(node):
    L = []
    while node is not None:
        ob = node.ob
        node = node.next
        L.append(ob)
    return L

def deserialize(L):
    reverse = L[::-1]
    node = None
    for ob in reverse:
        node = ListNode(ob, node)
    return node


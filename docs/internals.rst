=================================
 :mod:`repoze.session` Internals
=================================

The Session Manager
-------------------

The ``session manager`` implementation, (see
``repoze.session.manager.SessionDataManager``) stores session data
objects (aka "session objects", see
``repoze.session.data.SessionData``) within a ZODB database in a
singly-linked list (see ``repoze.session.linkedlist``) of "buckets",
where each bucket is a tuple representing the creation timestamp of
the tuple, and the OOBTree containing the session objects accessed
during that time period::


      +======================+           +============+ ?
      |  SessionDataManager  |     head  | ListNode   |------+
      |                      |-----------|            |      |
      |                      |         1 |            |<-----+
      +======================+           +============+ next
                                               |
                                            ob | 1
                                       +=============+
                                       | tuple       |
                                       |             |
                                       |             |
                                       +=============+
                                              |
                                   +----------+---------+
                                   |                    |
                             +=============+     +=============+
                             | timestamp   |     | OOBTree     |
                             |             |     |             |
                             |             |     |             |
                             +=============+     +=============+

Searching the Session Manager
-----------------------------

When searching for a session object, the session first gets the
current head bucket.  If that head is older than the session manager's
:term:`period`, the session manager creates a *new* bucket and pushes
it onto the list as the new head (its 'next' is the old head).

The session manager then iterates through the list of buckets, until
one of the following is true:

  - The ``OOBTree`` in the bucket contains the key.  In this case, the
    corresponding SessionData object is copied forward into the "head"
    bucket and returned.

  - The ``timestamp`` in the current bucket is older than the session
    manager's ``timeout``; in this case, the session manager truncates
    the list, and then performs housekeeping (see "Linked-List
    Housekeeping" below) on the truncated tail of the list.

  - The list ends before finding the key.
  
In either of the last two cases, the session manager creates a new
session object for the key.  If the session manager is marked as
*lazy*, it sets a callback to copy the new SessionData object into the
"head" bucket's OOBTree when the transaction commits, if the
SessionData object has been modified.  If the session manager is *not*
lazy, it copies the new SessionData object into the head bucket
immediately.  In either case, the session manager also sends an
``ISessionBeginEvent``, passing the new SessionData object.

Session Manager Housekeeping
----------------------------

After discovering that a given bucket in its list represents an
"expired" timeslice, the session manager truncates the list, setting
the 'next' attribute of the oldest valid node to None.  The session
manager then processes the expired remainder as follows:

#. It first constructs a set, 'seen', containing the keys stored
   in the "valid" nodes.

#. For each expired node, it checks the keys in the node's OOBTree;
   for each key, if that key is not already seen, it sends an
   ``ISessionEndEvent`` passing the doomed SessionData object; it then
   adds the key to the "seen" set.

Session Manager Conflict Resolution
-----------------------------------

Near-simultaneous transactions may attempt to modify the linked list,
either by pushing a new head bucket, or else by truncating the list at
its oldest "valid" bucket.

- First, fail for conflicts on the period or timeout.

- Next, if either the 'new' version or the 'committed' version has
  obsoleted the 'old' version, fail.

- Finally, splice together the inserted nodes from the 'new' verision
  and inserted nodes from the 'committed' version (truncating the latter,
  if necessary).

Linked-List Serialization
-------------------------

In order to minimize the size of the pickle storing the linked list,
the list class serializes itself as a native Python list of pointers
to the objects.

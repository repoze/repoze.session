.. _usage:

=============================
 :mod:`repoze.session` Usage
=============================

:mod:`repoze.session` is sessioning system for Python web applications.

Using Session Data Objects and Expiration
-----------------------------------------

:mod:`repoze.session` automatically expires sessions which have been
inactive for some timeout.

Here is an example of using the sessioning machinery in one of your
applications:

.. literalinclude:: code/sample.py
   :linenos:
   :language: python

The value you send in to the session manager's ``get`` method should
be a value you've managed to assign to a particular user, perhaps via
a cookie.  See :term:`repoze.browserid` for a library that manages
browser identifiers.  These identifiers can be used as session manager
keys.

Using Begin and End Subscribers
-------------------------------

:mod:`repoze.session` allows you to register session-end and
session-begin subscribers in order to react to the start and end of a
session.

.. literalinclude:: code/subscribers.py
   :linenos:
   :language: python

Gotchas
-------

Values inserted into a :mod:`repoze.session` session store should not
subclass ZODB ``Persistent`` class.  If they do, there is a chance
that irresolveable cross-database references will put into the
session manager's (separate) database.

When the ``ConnectionManager`` 's ``commit`` method is called, it will
commit a transaction for all databases participating in Zope
transaction management.  Don't use this method if you already have
transaction management enabled in another way.

.. _api_module:

===========================
 :mod:`repoze.session` API
===========================

:mod:`repoze.session.manager`
=============================

.. automodule:: repoze.session.manager

  .. autoclass:: SessionDataManager
     :members:

  .. autoclass:: SessionBeginEvent
     :members:

  .. autoclass:: SessionEndEvent
     :members:

  .. autoclass:: FileStorageSessionManagerFactory
     :members:

  .. autoclass:: ConnectionManager
     :members:

:mod:`repoze.session.data`
==========================

.. automodule:: repoze.session.data

  .. autoclass:: SessionData
     :members:

     .. attribute:: last_modified

        Return the time the session data was last modified in
        integer seconds-since-the-epoch form.  Modification generally implies
        a call to one of the session data object's __setitem__ or __delitem__
        methods, directly or indirectly as a result of a call to
        update, clear, or other mutating data access methods.  This value
        can be assigned.

     .. attribute:: created

        Return the time the session data object was created in integer
        seconds-since-the-epoch form.  This attribute cannot be assigned.

  ``SessionData`` objects support the full Python dictionary interface
  (e.g. ``__getitem__``, ``__delitem__``, ``get``, ``has_key``, etc).


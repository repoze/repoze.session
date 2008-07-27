.. _glossary:

============================
Glossary
============================

.. glossary::

  Setuptools
    `Setuptools <http://peak.telecommunity.com/DevCenter/setuptools>`_
    builds on Python's ``distutils`` to provide easier building,
    distribution, and installation of packages.
  Interface
    An attribute of a model object that determines its type.  It is an
    instance of a ``zope.interface`` Interface class.
  Zope
    `The Z Object Publishing Framework <http://zope.org>`_.  The granddaddy 
    of Python web frameworks.
  ZODB
    `The Zope Object Database <http://wiki.zope.org/ZODB/FrontPage>`_
    which is a persistent object store for Python.
  Virtualenv
    An isolated Python environment.  Allows you to control which
    packages are used on a particular project by cloning your main
    Python.  `virtualenv <http://pypi.python.org/pypi/virtualenv>`_
    was created by Ian Bicking.
  Session
    A namespace that is valid for some period of continual activity
    that can be used to represent a user's interaction with a web application.
  faster
    The `Zope2 "faster" product
    <http://agendaless.com/Members/tseaver/software/faster/>`_ on which
    :mod:`repoze.session` is based.
  Period
    The number of seconds that implies a :term:`timeslice`.
    A ``SessionDataManager`` has a period.
  Timeout
    The number of seconds of inactivity that a session data object
    must undergo in order to be considered invalid.  A
    ``SessionDataManager`` has a timeout.
  Timeslice
    A concrete period of time which, in the case of
    :mod:`repoze.session` is used to compute whether a particular
    session data object is still valid.
  repoze.browserid
    A `library <http://pypi.python.org/pypi/repoze.browserid/0.1>`_
    which assigns unique identifiers to website visitors via cookies.

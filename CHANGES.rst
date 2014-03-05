Changelog
=========

0.3 (unreleased)
----------------

- Dropped use of ``_container`` key in conflict resolution in favor of the
  ``data`` key used since ZODB 3.9.0.

- Replaced deprecated ``zope.interface.implements`` usage with equivalent
  ``zope.interface.implementer`` decorator.

- Moved to GitHub.

- Updated docs/testing regime.

- Lazier commit behavior: try to compare session data last modified to old
  last modified; only reset the session data to the head if the modification
  times differ.

- Avoid setting ``last_modified`` in ``SessionData.setdefault`` unless the
  key was actually missing.

- Drop dependency on 'ZODB3'; depend on separately-released 'ZODB' and
  'persistent' instead.

- Added support for PyPy (any version supported by dependencies).

- Added support for Python 3.2 / 3.3.

- Dropped support for Python 2.4 and 2.5.

0.2 (2009-07-08)
----------------

- 100% test coverage.

- Changed index location.

- Pointed to docs in README.txt

0.1 (2008-07-27)
----------------

- Initial release.

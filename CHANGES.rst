Changelog
=========

1.0a1
-----

- Added support for Python 3.3.

- Replaced deprecated ``zope.interface.implements`` usage with equivalent
  ``zope.interface.implementer`` decorator.

- Dropped support for Python 2.4 and 2.5.

- Moved to GitHub.

- Updated docs/testing regime.

- Lazier commit behavior: try to compare session data last modified to old
  last modified; only reset the session data to the head if the modification
  times differ.

- Don't set last_modified in session data setdefault unless ``get`` returns
  the marker.

0.2
---

- 100% test coverage.

- Changed index location.

- Pointed to docs in README.txt

0.1
---

- Initial release.


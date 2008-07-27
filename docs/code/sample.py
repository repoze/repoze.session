from repoze.session.manager import FileStorageSessionManagerFactory
from repoze.session.manager import ConnectionManager

factory = FileStorageSessionManagerFactory('session.db', 'mysessions')

cm = ConnectionManager()
session_manager = factory(cm)
session_data = session_manager.get('abc')
session_data['first_name'] = 'fred'
session_data.invalidate()
session_data = session_manager.get('abc')
assert(not session_data.has_key('first_name'))  # we invalidated it
session_data['last_name'] = 'McDonough'
cm.commit() # we need to commit the session data into the storage

# session data will automatically expire (become invalid) after 20
# minutes of session inactivity.


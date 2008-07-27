from zope.interface import Interface
from zope.interface import Attribute

from zope.interface.common.mapping import IMapping

class ISessionDataManager(Interface):
    def query(k, default=None):
        """
        Return value associated with key k.  If value associated with
        k does not exist, return default.
        """

    def has_key(k):
        """
        Return true if manager has value associated with key k, else
        return false.
        """

    def get(k):
        """
        If an object already exists in the manager with key "k", it
        is returned.

        Otherwise, create a new subobject of the type supported by this
        container with key "k" and return it.
        """

class ISessionData(IMapping):
    """ Supports a mapping interface plus expiration- and container-related
    methods """
    def invalidate():
        """
        Invalidate (expire) the session data object.
        """

    def is_valid():
        """
        Return true if session data object is still valid, false if not.
        A session data object is valid if its invalidate method has not been
        called.
        """

    last_modified = Attribute("""\
        Return the time the session data was last modified in
        integer seconds-since-the-epoch form.  Modification generally implies
        a call to one of the session data object's __setitem__ or __delitem__
        methods, directly or indirectly as a result of a call to
        update, clear, or other mutating data access methods.  This value
        can be assigned.
        """)

    created = Attribute("""\
        Return the time the session data object was created in integer
        seconds-since-the-epoch form.  This attribute cannot be assigned.
        """)

class ISessionBeginEvent(Interface):
    """ An interface representing an event that happens when a session begins
    """

class ISessionEndEvent(Interface):
    """ An interface representing an event that happens when a session ends
    """    

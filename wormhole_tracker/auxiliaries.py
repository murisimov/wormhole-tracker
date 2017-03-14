import logging
import shelve
from functools import wraps

from settings import settings

def authenticated(func):
    @wraps(func)
    def wrapper(handler, *args, **kwargs):
        if handler.get_secure_cookie("auth_cookie"):
            return func(handler, *args, **kwargs)
        return handler.redirect('/sign')
    return wrapper

def get_user(user_id):
    db = shelve.open(settings['db_path'], writeback=True)
    user = db['users'].get(user_id)
    db.close()
    return user or {}


class Router(object):
    """
    Keeps movement states, such as previous location,
    map tree and system interconnections. Builds and
    updates map tree, updates system interconnections.
    """
    def __init__(self):
        self.previous = ""
        self.tree = {}
        self.connections = []

    def _bind(self, current):
        """
        AUXILIARY
        ---------
        Purpose:
            To add a tuple of connected systems to self.connections.
        Process:
            Checks if there are no such pair already in
            self.connections, appends new pair if so.
        """
        if ( (self.previous, current) not in self.connections
          and (current, self.previous) not in self.connections ):
            self.connections.append( (self.previous, current) )

    def _track(self, location, systems):
        """
        AUXILIARY
        ---------
        Purpose:
            To provide list of keys that eventually lead to
            container of current system inside map-dict, so
            we could add new system to the route, therefore
            to update our map.
        Process:
            DANGER: RECURSIVE (:D)
            Once the location is reached("else" block), it returns initial
            list with location itself. This, in turn, triggers chain return,
            and on each return previous system name inserts before the next.
        """
        if location not in systems:
            # Means that destination isn't reached yet.
            # Let us try to find it further.
            for name, inner_systems in systems.items():
                chain = self._track(location, inner_systems)
                if chain:
                    chain.insert(0, name)
                    return chain
        else:
            # Seems like this is the end of the way
            return [location]

    def build_map(self, current):
        """
        PUBLIC
        ------
        Purpose:
            To build the map tree depending on previous and current locations.
        Process:
            Check location state within control flow.
            - Do nothing if we are in the same place;
            - Only change location state if system is already in the map tree;
            - Update the map tree and change location state if system is new;
            - Create entry point in the map tree if there is no systems yet.
        """
        if self.previous == current:
            # We are in the same system!
            pass

        elif self._track(current, self.tree):
            # We have already been here, tree does not need an update.
            # But just in case we should update interconnections!
            self._bind(current)
            self.previous = current

        elif self._track(self.previous, self.tree):
            # We have not been here yet, let's extend the map tree.
            chain = self._track(self.previous, self.tree)
            path = self.tree
            for system in chain:
                path = path[system]
            else:
                path[current] = {}
                self._bind(current)
                self.previous = current
        else:
            # This is a new route!
            self.tree[current] = {}
            self.previous = current

        return self._treantify('--------', self.tree)

    def _treantify(self, sysname, sysobject):
        """
        AUXILIARY
        ---------
        Purpose:
            To rebuild the route to data structure that Treant.js can handle
        """
        result = {
            'text': {'name': sysname},
            'children': [],
        }
        for sys in sysobject:
            child = sysobject[sys]
            converted = self._treantify(sys, child)
            result['children'].append(converted)
        return result

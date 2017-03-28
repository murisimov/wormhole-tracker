#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#
# This file is part of wormhole-tracker package released under
# the GNU GPLv3 license. See the LICENSE file for more information.

import logging
import shelve
from functools import wraps
from os import urandom

from settings import settings


def token_gen():
    b64encoded = urandom(24).encode('base-64')
    return unicode(b64encoded.strip(), 'utf-8')


def authenticated(func):
    """
    Wrap Tornado RequestHandler methods
    to provide simple authentication
    
    :arg func: tornado request handler method
    :return: wrapped handler that redirects
    unauthenticated users to the login page
    """
    @wraps(func)
    def wrapper(handler, *args, **kwargs):
        if handler.get_secure_cookie("auth_cookie"):
            return func(handler, *args, **kwargs)
        return handler.redirect('/sign')
    return wrapper


class Router(object):
    """
    Keeps movement states, such as previous location,
    map tree and system interconnections. Builds and
    updates map tree, updates system interconnections.
    """
    def __init__(self, user_id, app):
        self.user_id = user_id  # User's id, will be used to get user object
        self.application = app  # Application object
        self.previous = ""      # Player's location fetched on the last API call
        self.connections = []   # List with tuples of all star system interconnections
        self.systems = []       # List with all visited systems

    def _update(self):
        """
        Save self to the user's object
        """
        self.application.update_user(self.user_id, {'router': self})

    def reset(self):
        """
        Reset routing info
        """
        self.previous = ""
        self.connections = []
        self.systems = []
        self._update()

    def update_map(self, current):
        """
        Check current location, update internal state if it
        is changed, return data for front-end graph drawing.
        
        :arg     current: users's current in-game location
        :return: dict with `current` location, node and link info for D3.js

        """
        if self.previous != current:
            result = {'current': current}
            if current not in self.systems:
                self.systems.append(current)
                result['node'] = {'name': current}

            if self.previous and (self.previous, current) not in self.connections:
                if (current, self.previous) not in self.connections:
                    self.connections.append((self.previous, current))
                    result['link'] = {
                        'source': self.previous,
                        'target': current
                    }
            self.previous = current
            # Since router object has changed we need to update user data
            self._update()
            return result

    def recover_map(self):
        pass

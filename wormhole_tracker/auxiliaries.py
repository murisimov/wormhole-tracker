#!/usr/bin/env python3.6
# -*- coding: utf-8 -*-
#
# This file is part of wormhole-tracker package released under
# the GNU GPLv3 license. See the LICENSE file for more information.

import logging
from base64 import b64encode
from functools import wraps
from os import urandom


def a(string):
    return string.encode('ascii')


def s(string):
    if isinstance(bytes, string):
        return string.decode('utf-8')
    else:
        return str(string)


async def token_gen():
    return b64encode(urandom(24)).strip()


def authenticated(func):
    """
    Wrap Tornado RequestHandler methods
    to provide simple authentication
    
    :argument func: tornado request handler method
    :return: wrapped handler that redirects
    unauthenticated users to the login page
    """
    @wraps(func)
    def wrapper(handler, *args, **kwargs):
        cookie = handler.get_secure_cookie("auth_cookie")
        if cookie:
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
        self.recovery = {       # Storage for front-end data, required for recovery
            'nodes': [], 'links': []
        }

    async def _save(self):
        """
        Save self to the user's object
        """
        self.application.users.get(
            self.user_id, {}).update(
            {'router': self}
        )

    async def update(self, current):
        """
        Check current location, update internal state if it
        is changed, return data for front-end graph drawing.
        
        :argument     current: users's current in-game location
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
            await self._save()
            return result

    async def backup(self, data):
        self.recovery = data
        await self._save()

    async def reset(self):
        """
        Reset routing info
        """
        self.previous = ""
        self.connections = []
        self.systems = []
        await self._save()

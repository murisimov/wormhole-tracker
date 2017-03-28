#!/usr/bin/env python3.6
# -*- coding: utf-8 -*-
#
# This file is part of wormhole-tracker package released under
# the GNU GPLv3 license. See the LICENSE file for more information.

import logging
import shelve
from functools import wraps
from multiprocessing import cpu_count
from os import urandom

from tornado.concurrent import futures, run_on_executor
from tornado.gen import coroutine, Return

from settings import settings


def token_gen():
    b64encoded = urandom(24).encode('base-64')
    return unicode(b64encoded.strip(), 'utf-8')


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
        self.recovery = {       # Storage for front-end data, required for recovery
            'nodes': [], 'links': []
        }

    @coroutine
    def _save(self):
        """
        Save self to the user's object
        """
        yield self.application.crud.update_user(
            self.user_id, {'router': self}
        )

    @coroutine
    def update(self, current):
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
            yield self._save()
            raise Return(result)

    @coroutine
    def backup(self, data):
        self.recovery = data
        yield self._save()

    @coroutine
    def reset(self):
        """
        Reset routing info
        """
        self.previous = ""
        self.connections = []
        self.systems = []
        yield self._save()


class ManageShelve(object):
    def __init__(self):
        self.executor = futures.ThreadPoolExecutor(
            max_workers=cpu_count()
        )

    @coroutine
    def get_user(self, user_id):
        """
        Retrieve user

        :argument user_id: user id
        :return: user object
        """
        db = shelve.open(
            settings['db_path']
        )
        user = db['users'].get(user_id)
        db.close()
        raise Return(user or {})

    @coroutine
    def update_user(self, user_id, data):
        """
        Update user object

        :argument user_id: user id
        :argument data: dict with data to update
        :return updated user object
        """
        # Use writeback=True to actually
        # save changes on db close
        db = shelve.open(
            settings['db_path'],
            writeback=True
        )
        if not db['users'].get(user_id):
            db['users'][user_id] = {}
        db['users'][user_id].update(data)
        user = db['users'].get(user_id)
        db.close()
        raise Return(user or {})

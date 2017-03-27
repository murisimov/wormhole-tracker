#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#
# This file is part of wormhole-tracker package released under
# the GNU GPLv3 license. See the LICENSE file for more information.

import logging
import shelve
from functools import wraps

from settings import settings


def authenticated(func):
    """
    
    :arg func:  
    :return: 
    """
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
        self.previous = ""     # Player's location fetched on the last API call
        self.connections = []  # List with tuples of all star system interconnections
        self.systems = []      # List with all visited systems

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
            return result

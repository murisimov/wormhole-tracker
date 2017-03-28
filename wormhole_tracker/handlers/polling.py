#!/usr/bin/env python3.6
# -*- coding: utf-8 -*-
#
# This file is part of wormhole-tracker package released under
# the GNU GPLv3 license. See the LICENSE file for more information.

import logging

from tornado.escape import json_decode
from tornado.gen import coroutine
from tornado.ioloop import PeriodicCallback

from wormhole_tracker.handlers.base_socket import BaseSocketHandler


class PollingHandler(BaseSocketHandler):
    """
    This class represents user, connected via websocket.
    """
    def __init__(self, *args, **kwargs):
        """
        Trigger parent's __init__ and register periodic
        callback which will be used for tracking
        """
        super(PollingHandler, self).__init__(*args, **kwargs)
        # Set Tornado PeriodicCallback with our self.track, we
        # will use launch it later on track/untrack commands
        self.tracker = PeriodicCallback(self.track, 5000)

    @coroutine
    def track(self):
        """
        This is actually the tracking function. When user pushes "track",
        PeriodicCallback starts and fires once in 5 second, makes an API
        call and updates changed router. And stops on "untrack" action.
        """
        # Call API to find out current character location
        location = yield self.character(self.user_id, '/location/', 'GET')

        if location:
            user = yield self.user
            graph_data = yield user['router'].update(
                location['solarSystem']['name']
            )
            if graph_data:
                message = ['update', graph_data]
                logging.warning(graph_data)
                yield self.safe_write(message)
        else:
            message = ['warning', 'Log into game to track your route']
            yield self.safe_write(message)

    @coroutine
    def open(self):
        """
        Triggers on successful websocket connection
        """
        if self.user_id:
            self.vagrants.append(self)
            logging.info("Connection received from " + self.request.remote_ip)

            user = yield self.user
            yield self.safe_write(['recover', user['router'].recovery])
        else:
            self.close()

    @coroutine
    def on_message(self, message):
        """
        Triggers on receiving front-end message
        
        :argument message: front-end message
        
        Receive user commands here
        """
        user = yield self.user

        logging.info(message)
        message = json_decode(message)
        if message == 'track':
            # Start the PeriodicCallback
            if not self.tracker.is_running():
                self.tracker.start()

        elif message in ['stop', 'reset']:
            if self.tracker.is_running():
                self.tracker.stop()
            if message == 'reset':
                yield user['router'].reset()

        elif message[0] == 'backup':
            yield user['router'].backup(message[1])

    @coroutine
    def on_close(self):
        """
        Triggers on closed websocket connection
        """
        self.vagrants.remove(self)
        if self.tracker.is_running():
            self.tracker.stop()
        logging.info("Connection closed, " + self.request.remote_ip)

#!/usr/bin/env python3.6
# -*- coding: utf-8 -*-
#
# This file is part of wormhole-tracker package released under
# the GNU GPLv3 license. See the LICENSE file for more information.

import logging

from tornado.escape import json_decode
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

    async def track(self):
        """
        This is actually the tracking function. When user pushes "track",
        PeriodicCallback starts and fires once in 5 second, makes an API
        call and updates changed router. And stops on "untrack" action.
        """
        # Call API to find out current character location
        location = await self.character(self.user_id, '/location/', 'GET')

        if location:
            user = self.user
            graph_data = await user['router'].update(
                location['solarSystem']['name']
            )
            if graph_data:
                message = ['update', graph_data]
                logging.warning(graph_data)
                await self.safe_write(message)
        else:
            message = ['warning', 'Log into game to track your route']
            await self.safe_write(message)

    def open(self):
        """
        Triggers on successful websocket connection
        """
        if self.user_id:
            self.vagrants.append(self)
            logging.info("Connection received from " + self.request.remote_ip)

            user = self.user
            self.spawn(self.safe_write, ['recover', user['router'].recovery])
        else:
            self.close()

    def on_message(self, message):
        """
        Triggers on receiving front-end message
        
        :argument message: front-end message
        
        Receive user commands here
        """
        user = self.user

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
                self.spawn(user['router'].reset)

        elif message[0] == 'backup':
            self.spawn(user['router'].backup, message[1])

    def on_close(self):
        """
        Triggers on closed websocket connection
        """
        self.vagrants.remove(self)
        if self.tracker.is_running():
            self.tracker.stop()
        logging.info("Connection closed, " + self.request.remote_ip)

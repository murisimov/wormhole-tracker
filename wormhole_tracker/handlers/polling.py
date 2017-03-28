#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#
# This file is part of wormhole-tracker package released under
# the GNU GPLv3 license. See the LICENSE file for more information.

import logging

from tornado.escape import json_decode
from tornado.gen import coroutine, sleep

from wormhole_tracker.auxiliaries import get_user
from wormhole_tracker.handlers.base_socket import BaseSocketHandler


class PollingHandler(BaseSocketHandler):
    def __init__(self, *args, **kwargs):
        super(PollingHandler, self).__init__(*args, **kwargs)
        self.tracking = False

    @coroutine
    def run(self):
        router = get_user(self.user_id)['router']
        self.tracking = True
        while self.tracking:
            # Make a request to find out current location
            location = yield self.character(self.user_id, '/location/', 'GET')

            if location:
                graph_data = router.update_map(location['solarSystem']['name'])
                #logging.warning(graph_data)
                message = ['graph', graph_data or {}]
            else:
                message = ['warning', 'Log into game to track your route']

            result = yield self.safe_write(message)
            if result:
                yield sleep(5)
            else:
                # In that case connection is already closed
                self.tracking = False

    def open(self):
        if self.user_id:
            self.tracking = False
            self.vagrants.append(self)
            logging.info("Connection received from " + self.request.remote_ip)
        else:
            self.close()

    @coroutine
    def on_message(self, message):
        logging.info(message)
        message = json_decode(message)
        if message == 'track':
            if not self.tracking:
                yield self.run()
        elif message == 'stop':
            self.tracking = False

    def on_close(self):
        self.vagrants.remove(self)
        logging.info("Connection closed, " + self.request.remote_ip)

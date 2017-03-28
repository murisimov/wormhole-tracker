#!#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#
# This file is part of wormhole-tracker package released under
# the GNU GPLv3 license. See the LICENSE file for more information.

import logging

from tornado.escape import json_encode
from tornado.gen import coroutine, Return
from tornado.websocket import WebSocketHandler


class BaseSocketHandler(WebSocketHandler):
    @property
    def client_id(self):
        return self.application.client_id

    @property
    def client_key(self):
        return self.application.client_key

    @property
    def vagrants(self):
        return self.application.vagrants

    @property
    def state_storage(self):
        return self.application.state_storage

    @property
    def user_id(self):
        return self.get_secure_cookie("auth_cookie")

    @property
    def user(self):
       return self.application.get_user(self.user_id)

    @property
    def authorize(self):
        return self.application.authorize

    @property
    def character(self):
        return self.application.character

    @coroutine
    def safe_write(self, message):
        if self.ws_connection is None:
            logging.error('Connection is already closed.')
            raise Return(False)
        else:
            self.write_message(json_encode(message))
            raise Return(True)

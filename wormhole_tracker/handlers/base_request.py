#!/usr/bin/env python3.6
# -*- coding: utf-8 -*-
#
# This file is part of wormhole-tracker package released under
# the GNU GPLv3 license. See the LICENSE file for more information.

from tornado.gen import coroutine, Return
from tornado.web import RequestHandler


class BaseHandler(RequestHandler):
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
    def crud(self):
        return self.application.crud

    @property
    def user_id(self):
        return self.get_secure_cookie("auth_cookie")

    @property
    @coroutine
    def user(self):
        user = yield self.application.get_user(self.user_id)
        raise Return(user)

    @property
    def authorize(self):
        return self.application.authorize

    @property
    def character(self):
        return self.application.character

#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#
# This file is part of wormhole-tracker package released under
# the GNU GPLv3 license. See the LICENSE file for more information.

import logging

from tornado.gen import coroutine

from wormhole_tracker.handlers.base_request import BaseHandler
from wormhole_tracker.auxiliaries import authenticated, get_user


class SignHandler(BaseHandler):
    @coroutine
    def get(self):
        self.render("sign.html")


class MainHandler(BaseHandler):
    @authenticated
    @coroutine
    def get(self, *args, **kwargs):
        kwargs = {
            'hostname': self.request.host,
            'user': get_user(self.user_id)
        }
        self.render("main.html", **kwargs)


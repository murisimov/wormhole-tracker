# -*- coding: utf-8 -*-
#
# This file is part of wormhole-tracker package released under
# the GNU GPLv3 license. See the LICENSE file for more information.

import logging

from wormhole_tracker.auxiliaries import authenticated
from wormhole_tracker.handlers.base_request import BaseHandler


class SignHandler(BaseHandler):
    async def get(self):
        self.render("sign.html")


class MainHandler(BaseHandler):
    @authenticated
    async def get(self, *args, **kwargs):
        user = self.user
        kwargs = {
            'hostname': self.request.host,
            'user': user
        }
        self.render("main.html", **kwargs)

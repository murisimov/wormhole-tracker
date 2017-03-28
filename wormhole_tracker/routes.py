#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#
# This file is part of wormhole-tracker package released under
# the GNU GPLv3 license. See the LICENSE file for more information.

import wormhole_tracker.handlers.pages as pages
import wormhole_tracker.handlers.actions as actions
import wormhole_tracker.handlers.polling as polling

routes = [
    (r"/",          pages.MainHandler),
    (r"/sign",      pages.SignHandler),
    (r"/signin",    actions.SigninHandler),
    (r"/auth/(.*)", actions.AuthHandler),
    (r"/signout",   actions.SignoutHandler),
    (r"/poll",      polling.PollingHandler),
]

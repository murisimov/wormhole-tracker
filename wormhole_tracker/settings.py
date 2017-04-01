# -*- coding: utf-8 -*-
#
# This file is part of wormhole-tracker package released under
# the GNU GPLv3 license. See the LICENSE file for more information.

from base64 import b64encode
from os import urandom
from pkg_resources import resource_filename


settings = {
    'static_path': resource_filename('wormhole_tracker', 'static'),
    'template_path': resource_filename('wormhole_tracker', 'templates'),
    #'cookie_secret': b64encode(urandom(24)).strip(),
    'login_url': '/sign',
}

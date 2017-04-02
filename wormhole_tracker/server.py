#!/usr/bin/env python3.6
# -*- coding: utf-8 -*-
#
# This file is part of wormhole-tracker package released under
# the GNU GPLv3 license. See the LICENSE file for more information.

import logging
import shelve
from base64 import b64encode
from os import sys

from tornado.escape import json_decode, json_encode
from tornado.httpclient import AsyncHTTPClient, HTTPError, HTTPRequest
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from tornado.options import (
    define, options, parse_command_line, parse_config_file
)
from tornado.web import Application

from wormhole_tracker.auxiliaries import a, Router
from wormhole_tracker.routes import routes
from wormhole_tracker.settings import settings

define('port', 13131, int)
define('client_id')
define('client_key')
define('redirect_uri')
define('cookie_secret', 'default_secret')

http_client = AsyncHTTPClient()


class App(Application):
    def __init__(self, client_id, client_key, routes, settings):
        """
        Instantiate application object
        
        :argument client_id:   EVE app Client ID
        :argument client_key:  EVE app Secret Key
        Both application id and secret key, which can
        be obtained at https://developers.eveonline.com
        """
        super(App, self).__init__(routes, **settings)
        self.client_id = client_id
        self.client_key = client_key
        self.vagrants = []
        self.state_storage = {}
        self.users = {}  # Temporary users storage

    def spawn(self, callback, *args, **kwargs):
        """
        Shortcut for spawning callback on IOLoop
        
        Since WebSocketHandler main methods do not support
        async, while we still don't want to block anything,
        we call IOLoop.spawn_callback for help - once we
        passed a callback it will be executed on the next
        IOLoop iteration.
        
        :argument callback: callback to call
        :argument args:     callback arguments
        :argument kwargs:   key word arguments
        """
        IOLoop.current().spawn_callback(callback, *args, **kwargs)

    async def authorize(self, code, refresh=False):
        """
        Authorize user via API and get/refresh credentials data
        
        :argument code:   either user's 'authorization_code' or 'refresh_token'
        :argument refresh:     do we need to use the `code` as a refresh_token?
        
        1. Get access token with the  `code`
        2. Verify the access token and get character info
        3. Set or update character database data
        4. :return user id in case of success
        """
        ''' 1 '''
        authorization = "https://login.eveonline.com/oauth/token"
        auth_string = a(f"{self.client_id}:{self.client_key}")
        credentials = b64encode(auth_string)
        headers = {
            'Authorization': a("Basic ") + credentials,
            'Content-Type': 'application/json',
            'Host': "login.eveonline.com"
        }
        if not refresh:
            body = json_encode({
                'grant_type': 'authorization_code',
                'code': code
            })
        else:
            body = json_encode({
                'grant_type': 'refresh_token',
                'refresh_token': code
            })
        request = HTTPRequest(
            authorization,
            method="POST",
            headers=headers,
            body=body
        )
        try:
            response = await http_client.fetch(request)
            #logging.warning(response)
            logging.info(response.body)
            tokens = json_decode(response.body)
        except HTTPError as e:
            logging.error(e)
        else:
            ''' 2 '''
            verify = "https://login.eveonline.com/oauth/verify"
            headers = {
                'Authorization': 'Bearer ' + tokens['access_token'],
                'Host': 'login.eveonline.com'
            }
            request = HTTPRequest(verify, headers=headers)
            try:
                response = await http_client.fetch(request)
            except HTTPError as e:
                logging.error(e)
            else:
                charinfo = json_decode(response.body)
                user_id = str(charinfo['CharacterID'])
                try:
                    user = self.users.get(user_id)
                    ''' 3 '''
                    if not user:
                        self.users[user_id] = {}
                        user = charinfo
                        user['router'] = Router(user_id, self)

                    user['access_token']  = tokens['access_token']
                    user['refresh_token'] = tokens['refresh_token']

                    self.users[user_id].update(user)
                except Exception as e:
                    logging.error(f"ERROR OCCURRED: {e}")
                else:
                    ''' 4 '''
                    return user_id

    async def character(self, user_id, uri, method):
        """
        Fetch specific character info, re-authorize
        via API if access token became obsolete.
        
        :argument user_id: user id
        :argument uri:     uri to fetch (/location/ in our case)
        :argument method:  HTTP method
        :return:  fetched data (dict with location info)
        """
        user = self.users[user_id]
        url = (
            "https://crest-tq.eveonline.com/characters/" +
            str(user['CharacterID']) + uri
        )
        headers = {
            'Authorization': 'Bearer ' + user['access_token']
        }
        request = HTTPRequest(
            url,
            headers=headers,
            method=method,
            allow_nonstandard_methods=(method != 'GET')
        )
        logging.debug('Fetching character related data')
        try:
            response = await http_client.fetch(request)
        except HTTPError as e:
            if e.code == 401:
                logging.warning("Access token became obsolete, re-authorizing.")

                # Authorize again using refresh_token
                user_id = await self.authorize(
                    user['refresh_token'], refresh=True
                )
                # And then refresh user object
                user = self.users[user_id]
                headers['Authorization'] = 'Bearer ' + user['access_token']
                try:
                    response = await http_client.fetch(request)
                except HTTPError as e:
                    logging.error(f"UNEXPECTED ERROR OCCURRED: {e}")
                else:
                    return json_decode(response.body)
            elif e.code == 503:
                if e.response:
                    logging.warning(e.response)
        else:
            logging.debug(response)
            return json_decode(response.body)


def main():
    try:
        parse_config_file('/etc/wormhole-tracker.conf')
    except Exception as e:  # TODO: specify correct exception here
        logging.warning(e)
        parse_command_line()

    if (not options.client_id
      or not options.client_key
      or not options.redirect_uri
      or not options.cookie_secret):
        error = """

Please create configuration file /etc/wormhole-tracker.conf and fill it as follows:

    client_id     = "your_eve_app_id"
    client_key    = "your_eve_app_key"
    redirect_uri  = "http://your-domain-or-ip.com"
    cookie_secret = "my_secret_secret"

For example:

    client_id     = "334jjnn32i23yv23592352352sa3n52b"
    client_key    = "3534ui32b5223yu5u2v35v23v523v3fg"
    redirect_uri  = "http://my-awesome-eve-app.com" # the "http(s)://" IS required!
    cookie_secret = "WYkRXG1RJhmpYlYCA2D99EFRz9lt709t"

Or provide this data as command line arguments as follows:

    wormhole-tracker --client_id="eve_app_id" \\
                     --client_key="eve_app_key" \\
                     --redirect_uri="https://domain-or-ip.com" \\
                     --cookie_secret="my_secret"

        """
        logging.error(error)
        sys.exit(1)

    settings['cookie_secret'] = options.cookie_secret
    app = App(options.client_id, options.client_key, routes, settings)
    http_server = HTTPServer(app, xheaders=True)

    # TODO: uncomment when obtain db
    #http_server.bind(options.port)
    #http_server.start(0)  # Use one IOLoop per CPU core
    http_server.listen(options.port)

    try:
        logging.info("Starting server...")
        IOLoop.current().start()
    except (SystemExit, KeyboardInterrupt):
        logging.info("Stopping server.")
        IOLoop.current().stop()
        http_client.close()
        sys.exit()

    except Exception as e:
        logging.error(e)
        IOLoop.current().stop()
        http_client.close()
        sys.exit(1)

if __name__ == '__main__':
    main()

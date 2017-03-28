#!/usr/bin/env python3.6
# -*- coding: utf-8 -*-
#
# This file is part of wormhole-tracker package released under
# the GNU GPLv3 license. See the LICENSE file for more information.

import logging
import shelve
import urllib2

from base64 import b64encode
from datetime import datetime
from multiprocessing import cpu_count
from os import sys
from os.path import dirname, join
from time import time
from urllib import urlencode, unquote

from tornado.escape import json_decode, json_encode, url_escape
from tornado.gen import coroutine, Return, sleep, Task
from tornado.ioloop import IOLoop
from tornado.httpclient import AsyncHTTPClient, HTTPError, HTTPRequest
from tornado.httpserver import HTTPServer
from tornado.options import define, options, parse_command_line, parse_config_file
from tornado.web import Application

from wormhole_tracker.auxiliaries import Router, ManageShelve
from wormhole_tracker.routes import routes
from wormhole_tracker.settings import settings

define('port', 13131, int)
define('client_id')
define('client_key')
define('redirect_uri')

http_client = AsyncHTTPClient()


class App(Application):
    def __init__(self, client_id, client_key):
        """
        Instantiate application object
        
        :argumentument client_id:   EVE app Client ID
        :argumentument client_key:  EVE app Secret Key
        Both application id and secret key, which can
        be obtained at https://developers.eveonline.com
        """
        super(App, self).__init__(routes, **settings)
        self.client_id = client_id
        self.client_key = client_key
        self.vagrants = []
        self.state_storage = {}
        self.crud = ManageShelve()

    @coroutine
    def authorize(self, code, refresh=False):
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
        credentials = b64encode(self.client_id + ':' + self.client_key)
        headers = {
            'Authorization': "Basic " + credentials,
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
            response = yield http_client.fetch(request)
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
                response = yield http_client.fetch(request)
            except HTTPError as e:
                logging.error(e)
            else:
                charinfo = json_decode(response.body)
                user_id = str(charinfo['CharacterID'])
                try:
                    user = yield self.crud.get_user(user_id)
                    ''' 3 '''
                    if not user:
                        user = charinfo
                        user['router'] = Router(user_id, self)

                    user['access_token']  = tokens['access_token']
                    user['refresh_token'] = tokens['refresh_token']

                    yield self.crud.update_user(user_id, user)
                except Exception as e:
                    logging.error(e)
                else:
                    ''' 4 '''
                    raise Return(user_id)

    @coroutine
    def character(self, user_id, uri, method):
        """
        Fetch specific character info, re-authorize
        via API if access token became obsolete.
        
        :argument user_id: user id
        :argument uri:     uri to fetch (/location/ in our case)
        :argument method:  HTTP method
        :return:      fetched data (dict with location info)
        """
        user = yield self.crud.get_user(user_id)
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
            response = yield http_client.fetch(request)
        except HTTPError as e:
            logging.error(e)
            # Authorize again with refresh_token
            yield self.authorize(user['refresh_token'], refresh=True)
            # And then refresh user object
            user = yield self.crud.get_user(user_id)
            headers['Authorization'] = 'Bearer ' + user['access_token']
            try:
                response = yield http_client.fetch(request)
            except HTTPError as e:
                logging.error(e)
            else:
                raise Return(json_decode(response.body))
        else:
            logging.debug(response)
            raise Return(json_decode(response.body))


def main():
    try:
        parse_config_file('/etc/wormhole-tracker.conf')
    except: # TODO: specify correct exception here
        parse_command_line()

    if not options.client_id or not options.client_key or not options.redirect_uri:
        error = """

Please create configuration file /etc/wormhole-tracker.conf and fill it as follows:

    client_id    = "your_eve_app_id"
    client_key   = "your_eve_app_key"
    redirect_uri = "http://your-domain-or-ip.com"

For example:

    client_id    = "334jjnn32i23yv23592352352sa3n52b"
    client_key   = "3534ui32b5223yu5u2v35v23v523v3fg"
    redirect_uri = "http://my-awesome-eve-app.com" # the "http(s)://" IS required!

Or provide this data as command line arguments as follows:

    wormhole-tracker --client_id="eve_app_id" --client_key="eve_app_key" --redirect_uri="https://domain-or-ip.com"

        """
        logging.error(error)
        sys.exit(1)

    app = App(options.client_id, options.client_key)
    http_server = HTTPServer(app)
    http_server.listen(options.port)

    # Prepare DB
    db = shelve.open(app.settings['db_path'], writeback=True)
    db['users'] = {}
    db.close()

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

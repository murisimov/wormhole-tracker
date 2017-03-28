#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#
# This file is part of wormhole-tracker package released under
# the GNU GPLv3 license. See the LICENSE file for more information.

import logging
import shelve
import urllib2

from base64 import b64encode
from datetime import datetime
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
from tornado.web import RequestHandler, Application
from tornado.websocket import WebSocketHandler

from auxiliaries import token_gen, authenticated, get_user, Router
from settings import settings

define('port', 13131, int)
define('client_id')
define('client_key')
define('redirect_uri')

http_client = AsyncHTTPClient()


class App(Application):
    def __init__(self, client_id, client_key):
        """
        Instantiate application object
        
        :arg client_id:   EVE app Client ID
        :arg client_key:  EVE app Secret Key
        Both application id and secret key, which can
        be obtained at https://developers.eveonline.com
        """
        # TODO: move routes to the separate file
        routes = [
            (r"/", MainHandler),
            (r"/sign", SignHandler),
            (r"/signin", SigninHandler),
            (r"/auth/(.*)", AuthHandler),
            (r"/signout", SignoutHandler),
            (r"/poll", PollingHandler),
        ]
        super(App, self).__init__(routes, **settings)
        self.client_id = client_id
        self.client_key = client_key
        self.vagrants = []
        self.state_storage = {}

    @coroutine
    def authorize(self, code, refresh=False):
        """
        User authorization and user information update
        
        :arg code:   either user's 'authorization_code' or 'refresh_token'
        :arg refresh:     do we need to use the `code` as a refresh_token?
        
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
                    # Use writeback=True to actually save changes on db close
                    db = shelve.open(self.settings['db_path'], writeback=True)
                    ''' 3 '''
                    if not db['users'].get(user_id):
                        db['users'][user_id] = charinfo
                        db['users'][user_id]['router'] = Router()

                    db['users'][user_id].update({
                        'access_token': tokens['access_token'],
                        'refresh_token': tokens['refresh_token'],
                    })

                    logging.info(db['users'][user_id])

                    db.close()
                except Exception as e:
                    logging.error(e)
                else:
                    ''' 4 '''
                    raise Return(user_id)

    @coroutine
    def character(self, user_id, uri, method):
        user = get_user(user_id)
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
            user = get_user(user_id)
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
    def user_id(self):
        return self.get_secure_cookie("auth_cookie")

    @property
    def authorize(self):
        return self.application.authorize

    @property
    def character(self):
        return self.application.character


class SignHandler(BaseHandler):
    @coroutine
    def get(self):
        self.render("sign.html")


class SigninHandler(BaseHandler):
    @coroutine
    def get(self):
        """
        Triggers when user pushes "LOG IN with EVE Online" button at /sign;
        Redirects user to app's authorization page at EVE Online site;
        After providing credentials there, user being redirected to our /auth.
        """
        login_eveonline = "https://login.eveonline.com/oauth/authorize/?"

        # Generate state token and store it in the `state_storage`, this
        # way we will accept only our redirected users (CSRF protection)
        state = token_gen()
        self.state_storage[state] = datetime.now()

        query = urlencode({
            'response_type': 'code',
            'redirect_uri': '%s/auth/' % options.redirect_uri,
            'client_id': self.client_id,
            'scope': 'characterBookmarksRead characterLocationRead',
            #'scope': 'characterLocationRead',
            'state': state,
        })
        login_eveonline += query
        self.redirect(login_eveonline)


class AuthHandler(BaseHandler):
    @coroutine
    def get(self, *args, **kwargs):
        """
        Triggers when EVE Online site redirects user here, after providing
        credentials there. EVE provides us with "code" and "state" arguments;
        We need "code" to get user info, while "state" is needed for optional
        security purposes, which are not implemented yet.
        """
        state = self.get_argument("state")
        # Check if `state` was generated by our app
        state_registered = self.state_storage.pop(state, None)
        if state_registered:
            logging.info("Time elapsed since signin: %s" % (datetime.now() - state_registered))
            code = self.get_argument("code")
            user_id = yield self.authorize(code)
            if user_id:
                self.set_secure_cookie("auth_cookie", str(user_id))
            self.redirect('/')
        else:
            # Restrict access if not.
            self.set_status(403)
            self.redirect('/watchalookin')


class MainHandler(BaseHandler):
    @authenticated
    @coroutine
    def get(self, *args, **kwargs):
        kwargs = {
            'hostname': self.request.host,
            'user': get_user(self.user_id)
        }
        self.render("main.html", **kwargs)


class SignoutHandler(RequestHandler):
    @coroutine
    def get(self, *args, **kwargs):
        self.clear_cookie("auth_cookie")
        self.redirect('/sign')


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


class PollingHandler(BaseSocketHandler):
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


def main():
    try:
        parse_config_file('/etc/wormhole-tracker.conf')
    except:
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

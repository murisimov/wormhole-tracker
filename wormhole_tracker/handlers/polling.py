# -*- coding: utf-8 -*-
#
# This file is part of wormhole-tracker package released under
# the GNU GPLv3 license. See the LICENSE file for more information.

import logging

from tornado.escape import json_decode
from tornado.ioloop import PeriodicCallback
from tornado.queues import Queue

from wormhole_tracker.handlers.base_socket import BaseSocketHandler


class PollingHandler(BaseSocketHandler):
    """
    This class represents separate websocket connection.
    """
    def __init__(self, *args, **kwargs):
        """
        Trigger parent's __init__, register periodic callback which will
        be used for tracking, and queue for user tasks
        """
        super(PollingHandler, self).__init__(*args, **kwargs)
        # Set Tornado PeriodicCallback with our self.track, we
        # will use launch it later on track/untrack commands
        self.tracker = PeriodicCallback(self.track, 5000)
        self.q = Queue(maxsize=5)
        self.updating = False

    async def track(self):
        """
        This is actually the tracking function. When user pushes "track" button,
        PeriodicCallback starts and fires once in 5 seconds, makes an API call
        and updates changed router. And stops on "untrack" button action.
        """
        # Call API to find out current character location
        location = await self.character(self.user_id, '/location/', 'GET')

        if location:
            # Set `updating` flag to not accept periodic updates
            # from front-end, to not overwrite new data
            self.updating = True
            user = self.user
            graph_data = await user['router'].update(
                location['solarSystem']['name']
            )
            if graph_data:
                message = ['update', graph_data]
                logging.warning(graph_data)
                await self.safe_write(message)
            self.updating = False
        else:
            message = ['warning', 'Log into game to track your route']
            await self.safe_write(message)

    async def scheduler(self):
        """
        Scheduler for user tasks.
        
        Wait until there is new item in the queue, get job done, resolve task.
        Tornado queues doc: http://www.tornadoweb.org/en/stable/queues.html
        
        Since we have no guarantee of the order of the incoming messages (new
        message from front-end can come before current is done), we need to
        ensure all tasks to run successively.
        Here comes the asynchronous generator.
        """
        logging.info(f"Scheduler started for {self.request.remote_ip}")

        # Wait on each iteration until there's actually an item available
        async for item in self.q:
            #logging.info(f"Started resolving task for {item}...")
            user = self.user
            try:
                if item == 'recover':
                    # Send saved route
                    await self.safe_write(['recover', user['router'].recovery])

                elif item == 'track':
                    # Start the PeriodicCallback
                    if not self.tracker.is_running():
                        self.tracker.start()

                elif item in ['stop', 'reset']:
                    # Stop the PeriodicCallback
                    if self.tracker.is_running():
                        self.tracker.stop()
                    if item == 'reset':
                        await user['router'].reset()

                elif item[0] == 'backup':
                    # Do not overwrite user object while it's updating,
                    # just in case, to avoid race conditions.
                    if not self.updating:
                        await user['router'].backup(item[1])
            finally:
                self.q.task_done()
                #logging.warning(f'Task "{item}" done.')

    async def task(self, item):
        """
        Intermediary between `on_message` and `scheduler`.
        
        Since we cannot do anything asynchronous in the `on_message`, this
        method can handle any additional non-blocking stuff if we need it.
        
        :argument item: item to pass to the `scheduler`
        """
        await self.q.put(item)
        #await self.q.join()

    def open(self):
        """
        Triggers on successful websocket connection.
        
        Ensure user is authorized, spawn `scheduler` for user tasks, add this
        websocket object to the connections pool, spawn the recovery of the
        saved route.
        """
        logging.info(f"Connection received from {self.request.remote_ip}")
        if self.user_id:
            self.spawn(self.scheduler)
            self.vagrants.append(self)

            self.spawn(self.task, 'recover')
        else:
            self.close()

    def on_message(self, message):
        """
        Triggers on receiving front-end message.
        
        :argument message: front-end message
        
        Receive user commands here and pass 
        them to the `scheduler` via `task`
        """
        self.spawn(self.task, json_decode(message))

    def on_close(self):
        """
        Triggers on closed websocket connection.
        
        Remove this websocket object from the connections pool,
        stop `tracker` if it is running.
        """
        self.vagrants.remove(self)
        if self.tracker.is_running():
            self.tracker.stop()
        logging.info("Connection closed, " + self.request.remote_ip)

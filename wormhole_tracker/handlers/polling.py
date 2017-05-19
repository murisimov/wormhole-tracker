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
    
    Attributes:
        tracker: tornado.ioloop.PeriodicCallback with get_location method as a
            callback. Starts when user pushes "track" button. When started, it
            runs every 5 seconds to find out and update character's location.
            
        q: tornado.queues.Queue used for running tasks successively.
        
        updating: A flag indicates if router is being updated or not. Required
            to avoid race conditions.
    """
    def __init__(self, *args, **kwargs):
        super(PollingHandler, self).__init__(*args, **kwargs)
        # Set Tornado PeriodicCallback with our self.track, we
        # will use launch it later on track/untrack commands
        self.tracker = PeriodicCallback(self.get_location, 5000)
        self.q = Queue(maxsize=5)
        self.updating = False

    async def get_location(self):
        """
        The callback for the `self.tracker`.
        
        Makes an API call, updates router and sends updated data to the
        front-end.
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
        
        Waits until there is new item in the queue, does task, resolves task.
        Tornado queues doc: http://www.tornadoweb.org/en/stable/queues.html
        
        Since we have no guarantee of the order of the incoming messages
        (new message from front-end can come before current is done),
        we need to ensure all tasks to run successively.
        Here comes the asynchronous generator.
        """
        logging.info(f"Scheduler started for {self.request.remote_ip}")

        # Wait on each iteration until there's actually an item available
        async for item in self.q:
            logging.debug(f"Started resolving task for {item}...")
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
                    # Clear all saved data
                    if item == 'reset':
                        await user['router'].reset()

                elif item[0] == 'backup':
                    # Do not overwrite user object while it's updating,
                    # just in case, to avoid race conditions.
                    if not self.updating:
                        await user['router'].backup(item[1])
            finally:
                self.q.task_done()
                logging.debug(f'Task "{item}" done.')

    async def task(self, item):
        """
        Intermediary between `self.on_message` and `self.scheduler`.
        
        Since we cannot do anything asynchronous in the `self.on_message`,
        this method can handle any additional non-blocking stuff if we need it.
        
        :argument item: item to pass to the `self.scheduler`.
        """
        await self.q.put(item)
        #await self.q.join()

    def open(self):
        """
        Triggers on successful websocket connection.
        
        Ensures user is authorized, spawns `self.scheduler` for user
        tasks, adds this websocket object to the connections pool,
        spawns the recovery of the saved route.
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
        
        :argument message: front-end message.
        
        Receives user commands and passes them
        to the `self.scheduler` via `self.task`.
        """
        self.spawn(self.task, json_decode(message))

    def on_close(self):
        """
        Triggers on closed websocket connection.
        
        Removes this websocket object from the connections pool,
        stops `self.tracker` if it is running.
        """
        self.vagrants.remove(self)
        if self.tracker.is_running():
            self.tracker.stop()
        logging.info("Connection closed, " + self.request.remote_ip)


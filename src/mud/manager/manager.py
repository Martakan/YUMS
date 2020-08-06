#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Jul 19 15:21:04 2020

@author: AzureDVBB
"""

import asyncio

from mud.database import Database
from mud.password_hasher import PasswordHasher

from mud.player import Player
from mud.connection import Connection
from mud.commands import Interpreter

from mud import text
from mud import login_register


class Manager:

    def __init__(self):
        self.new_connections = []
        self.active_players = {}


    def initialize_inside_running_loop(self): # event loop dependant initialization
        # initialize database
        self.database = Database()
        self.interpreter = Interpreter(self.database)
        # initialize password_hasher
        self.password_hasher = PasswordHasher()


    async def add_connection(self, connection: Connection):
        self.new_connections.append(connection)
        await connection.write_queue.put(f"Welcome to the in-development mud game!"
                                         f"please enjoy your stay. \r\n"
                                         f"You can log in by typing: \r\n"
                                         f"login <name> <password>\r\n"
                                         f"Or register by typing:\r\n"
                                         f"register <name> <password>\r\n"
                                         f"Note that names should be lower case and cannot contain"
                                         f"spaces, passwords cannot contain spaces.")

        ######### Login and registration of new connections to a player object ####################
        ###########################################################################################
        attempts = 0
        max_attempts = 5
        while attempts < max_attempts:
            cmd = await connection.read_queue.get()
            segmented_command = text.split.cleanly(cmd)

            if len(segmented_command) != 3:
                attempts +=1
                await connection.write_queue.put(f"Command error: not understood {cmd}")
                continue

            command, name, password = segmented_command
            if command == 'login':
                result, message = await login_register.login(name, password,
                                                             self.database, self.password_hasher)
                await connection.write_queue.put(message)
                if not (result is False):
                    await self.add_player(connection, name, result)
                    break
                else:
                    attempts += 1

            elif command == 'register':
                await connection.write_queue.put(f"You are attempting to register with...\r\n"
                                                 f"name: {name}\r\n"
                                                 f"password: {password}\r\n"
                                                 f"Is this correct? Type: 'yes' or 'y' to confirm. "
                                                 f"Or cancel by typing 'no' 'n' or "
                                                 f"anything else really.")

                answer = await connection.read_queue.get()
                if answer.strip().lower() in ('yes', 'y'):
                    result, message = await login_register.register(name, password,
                                                                    self.database,
                                                                    self.password_hasher)
                else:
                    result = False
                    message = "Aborting..."
                await connection.write_queue.put(message)

                if result:
                    attempts = 0
                    continue
                else:
                    attempts += 1
                    continue

        if attempts >= max_attempts:
            connection.is_alive = False
        self.new_connections.remove(connection)

        return None # async spec
        ###########################################################################################


    async def __watch_commands(self, player: Player):
        while player.connections: # while there are still connections on player
            try: # wait for and interpret aggregate commands
                command = await asyncio.wait_for(player.command_queue.get(), 30)
                await self.interpreter.process(player, command)
            except asyncio.TimeoutError: # continue after a few seconds to check if player still conencted
                continue

        del self.active_players[player.character_name] # delete player ref
        print(f"player {player.character_name} disconnected")

        return None # async spec, has to have a return in there


    async def add_player(self, connection: Connection, name: str, character_document):
        if name in self.active_players:
            self.active_players[name].add_connection(connection)
        else:
            self.active_players[name] = Player(self.database, connection, character_document)
            asyncio.ensure_future(self.__watch_commands(self.active_players[name]))

        return None # as per async spec, has to return something
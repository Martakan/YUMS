#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Aug  1 16:57:35 2020

@author: AzureD

A collection of common database operations abstracted away.

This one is implements methods to interact and work with the Worlds and locations inside of them.
"""

import asyncio

from .datatypes.location import Location
from .datatypes.chatlog import LogEntry

class World:

    def __init__(self, database):
        self.database = database


    async def get_room_document_fields(self, location: Location, field_names: list):
        whitelisted_fields = {field: 1 for field in field_names} # works like a list comprehension

        world_name, coordinates = location.world_name, location.coordinates.asdict

        document = await self.database[world_name].find_one( # world_name collection in the database
                                                            {'coordinates': coordinates}, # get room by id
                                                            {'_id': 0, # do not get the document id
                                                             }.update(whitelisted_fields) # add whitelist
                                                            )

        # return None if document does not exist or document has no field with name: field_name
        return document if document else None


    async def get_room_document(self, location: Location) -> dict:
        world_name, coordinates = location.world_name, location.coordinates.asdict

        document = await self.database[world_name].find_one({'coordinates': coordinates},
                                                            {'_id': 0} # suppress id field
                                                            )

        # return None if document does not exist or document has no field with name: field_name
        return document if document else None

    async def get_room_document_id(self, location: Location):
        world_name, coordinates = location.world_name, location.coordinates.asdict

        key = await self.database[world_name].find_one({'coordinates': coordinates},
                                                       {'_id': 1} # ony bring back id field
                                                       )

        return key if key else None


    async def room_chatlog_add(self, location: Location, chat_name: str, log: LogEntry, max_log_size=20):
        world_name, coordinates = location.world_name, location.coordinates.asdict

        await self.database[world_name].update_one({'coordinates': coordinates}, # update the room at coords
                                                   {'$push': { # specify operation as 'push element into array'
                                                              f'chatlog.{chat_name}' : { # the path to the array (. as seperator in path)
                                                                                        '$each': [log.asdict], # each of these elements, needed for slice
                                                                                        '$slice': -max_log_size # ensure the max size is at most this many  of the LATEST elements
                                                                                        }
                                                              }
                                                    },
                                                   upsert=True # if the array does not exist yet, create it before performing the operations
                                                   )
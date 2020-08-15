#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Aug  5 10:19:13 2020

@author: AzureD
"""
# type hint references and IDE help
from mud.database import Database
from mud.manager import Manager

async def say(database: Database, manager: Manager, player_name: str, message: str):

    log_entry = database.datatypes.LogEntry(player_name, message)
    location = manager.player_manager.get_player_location(player_name)

    await database.world_helper_methods.room_chatlog_add(location, 'say', log_entry)

    await manager.connection_manager.send_message_to_many(manager.player_manager.players_in_location(location),
                                                          f'{player_name} says "{message}" '
                                                          f'eerily without echoes.'
                                                          )

    return None

COMMANDS = {'say': say}
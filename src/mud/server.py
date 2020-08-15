#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jul 14 08:45:42 2020

@author: AzureDVBB
"""

import asyncio
import socket

from .connection import Connection
from .manager import Manager

mng = Manager()

async def handle_connection(reader, writer):
    conn = Connection(reader, writer)
    await mng.authentication_manager.authenticate_connection(conn)
    print(f"Recieved new connection from {conn.address}")
    return None # conform with async def spec


async def main():
    mng.initialize_inside_running_loop() # finish initialization of manager inside the running loop

    server = await asyncio.start_server(handle_connection, '127.0.0.1', 8888,
                                        family=socket.AF_INET, flags=socket.AI_PASSIVE,
                                        reuse_address = 1, reuse_port = 1,
                                        ssl=None, ssl_handshake_timeout=None)

    addr = server.sockets[0].getsockname()
    print(f'Serving on {addr}')

    async with server:
        await server.serve_forever()

    return None # conform with async def spec


def run():
    asyncio.run(main())
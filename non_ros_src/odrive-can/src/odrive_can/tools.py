#!/usr/bin/env python3
"""
 Tools to assist with odrive development

 Copyright (c) 2023 ROX Automation - Jev Kuznetsov
"""
import time
import socket
import json
import logging


class UDP_Client:
    """send data to UDP server, used for plotting with plotjuggler"""

    def __init__(self, host: str = "127.0.0.1", port: int = 5005):
        self._host = host
        self._port = port
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        self._log = logging.getLogger(self.__class__.__name__)

    def send(self, data: dict, add_timestamp: bool = True):
        """send data to UDP server"""
        if add_timestamp:
            data["ts"] = time.time()

        try:
            self._sock.sendto(json.dumps(data).encode(), (self._host, self._port))
        except Exception as e:  # pylint: disable=broad-except
            self._log.error(f"Failed to send data: {e}")

# Based on ESP32 code Copyright (c) 2019 Matt Costi for Adafruit Industries
# SPDX-FileCopyrightText: Copyright (c) 2020 Patrick Van Oosterwijck
#
# SPDX-License-Identifier: MIT

"""
`adafruit_wiznet5k_wsgiserver`
================================================================================

A simple WSGI (Web Server Gateway Interface) server that interfaces with the W5500.
Opens a listening port on the W5500 to listen for incoming HTTP Requests and
Accepts an Application object that must be callable, which gets called
whenever a new HTTP Request has been received.

The Application MUST accept 2 ordered parameters:
    1. environ object (incoming request data)
    2. start_response function. Must be called before the Application
        callable returns, in order to set the response status and headers.

The Application MUST return strings in a list, which is the response data

Requires update_poll being called in the applications main event loop.

For more details about Python WSGI see:
https://www.python.org/dev/peps/pep-0333/

* Author(s): Matt Costi, Patrick Van Oosterwijck
"""
# pylint: disable=no-name-in-module
from __future__ import annotations

try:
    from typing import TYPE_CHECKING, Optional, List, Tuple, Dict

    if TYPE_CHECKING:
        from adafruit_wiznet5k.adafruit_wiznet5k import WIZNET5K
except ImportError:
    pass

import io
import gc
from micropython import const
import adafruit_wiznet5k as wiznet5k
import adafruit_wiznet5k.adafruit_wiznet5k_socket as socket

_the_interface: Optional[WIZNET5K] = None  # pylint: disable=invalid-name


def set_interface(iface: WIZNET5K) -> None:
    """
    Helper to set the global internet interface.

    :param wiznet5k.adafruit_wiznet5k.WIZNET5K: Ethernet interface.
    """
    global _the_interface  # pylint: disable=global-statement, invalid-name
    _the_interface = iface
    socket.set_interface(iface)


# pylint: disable=invalid-name
class WSGIServer:
    """A simple server that implements the WSGI interface."""

    def __init__(
        self,
        port: int = 80,
        debug: bool = False,
        application: Optional[callable] = None,
    ) -> None:
        """
        :param int port: WSGI server port, defaults to 80.
        :param bool debug: Enable debugging, defaults to False.
        :param Optional[callable] application: Application to call in response to a HTTP request.
        """
        self.application = application
        self.port = port
        self._timeout = 20
        self._client_sock = []
        self._debug = debug

        self._response_status = None
        self._response_headers = []
        if _the_interface.chip == "w5100s":
            self.MAX_SOCK_NUM = const(2)
        else:
            self.MAX_SOCK_NUM = const(6)
        if self._debug:
            print("Max sockets: ", self.MAX_SOCK_NUM)

    def start(self) -> None:
        """
        Start the server and listen for incoming connections.

        Call update_poll in the main loop for the application callable to be
        invoked on receiving an incoming request.
        """
        for _ in range(self.MAX_SOCK_NUM):
            new_sock = socket.socket()
            new_sock.settimeout(self._timeout)
            new_sock.bind((None, self.port))
            new_sock.listen()
            self._client_sock.append(new_sock)
        if self._debug:
            ip = _the_interface.pretty_ip(_the_interface.ip_address)
            print("Server available at {0}:{1}".format(ip, self.port))

    def update_poll(self) -> None:
        """
        Check for new incoming client requests.

        Call this method inside your main event loop to get the server
        check for new incoming client requests. When a request comes in,
        the application callable will be invoked.
        """
        for sock in self._client_sock:
            if sock._available():  # pylint: disable=protected-access
                environ = self._get_environ(sock)
                result = self.application(environ, self._start_response)
                self.finish_response(result, sock)
                self._client_sock.remove(sock)
                break
        for sock in self._client_sock:
            if (
                sock._status  # pylint: disable=protected-access
                == wiznet5k.adafruit_wiznet5k.SNSR_SOCK_CLOSED
            ):
                self._client_sock.remove(sock)
        for _ in range(len(self._client_sock), self.MAX_SOCK_NUM):
            try:
                new_sock = socket.socket()
                new_sock.settimeout(self._timeout)
                new_sock.bind((None, self.port))
                new_sock.listen()
                self._client_sock.append(new_sock)
            except RuntimeError:
                pass

    def finish_response(self, result: str, client: socket.socket) -> None:
        """
        Called after the application callable returns result data to respond with.
        Creates the HTTP Response payload from the response_headers and results data,
        and sends it back to client.

        :param str result: the data string to send back in the response to the client.
        :param socket.socket client: the socket to send the response to.
        """
        try:
            response = "HTTP/1.1 {0}\r\n".format(self._response_status)
            for header in self._response_headers:
                response += "{0}: {1}\r\n".format(*header)
            response += "\r\n"
            client.send(response.encode("utf-8"))
            for data in result:
                if not isinstance(data, bytes):
                    data = data.encode("utf-8")
                if len(data) < 0x800:
                    client.send(data)
                else:
                    # split to chunks of 2 kb
                    data_chunks = [
                        data[i : i + 0x800] for i in range(0, len(data), 0x800)
                    ]
                    for data_chunk in data_chunks:
                        client.send(data_chunk)
            gc.collect()
        finally:
            client._disconnect()  # pylint: disable=protected-access
            client.close()

    def _start_response(
        self, status: str, response_headers: List[Tuple[str, str]]
    ) -> None:
        """
        The application callable will be given this method as the second param
        This is to be called before the application callable returns, to signify
        the response can be started with the given status and headers.

        :param str status: a status string including the code and reason. ex: "200 OK"
        :param List[Tuple[str, str]] response_headers: a list of tuples to represent the headers.
            ex ("header-name", "header value")
        """
        self._response_status = status
        self._response_headers = [("Server", "w5kWSGIServer")] + response_headers

    def _get_environ(self, client: socket.socket) -> Dict:
        """
        The application callable will be given the resulting environ dictionary.
        It contains metadata about the incoming request and the request body ("wsgi.input")

        :param socket.socket client: Socket to read the request from.

        :return Dict: Data for the application callable.
        """
        env = {}
        line = str(client._readline(), "utf-8")  # pylint: disable=protected-access
        (method, path, ver) = line.rstrip("\r\n").split(None, 2)

        env["wsgi.version"] = (1, 0)
        env["wsgi.url_scheme"] = "http"
        env["wsgi.multithread"] = False
        env["wsgi.multiprocess"] = False
        env["wsgi.run_once"] = False

        env["REQUEST_METHOD"] = method
        env["SCRIPT_NAME"] = ""
        env["SERVER_NAME"] = _the_interface.pretty_ip(_the_interface.ip_address)
        env["SERVER_PROTOCOL"] = ver
        env["SERVER_PORT"] = self.port
        if path.find("?") >= 0:
            env["PATH_INFO"] = path.split("?")[0]
            env["QUERY_STRING"] = path.split("?")[1]
        else:
            env["PATH_INFO"] = path

        headers = {}
        while True:
            header = str(
                client._readline(), "utf-8"  # pylint: disable=protected-access
            )
            if header == "":
                break
            title, content = header.split(": ", 1)
            headers[title.lower()] = content

        if "content-type" in headers:
            env["CONTENT_TYPE"] = headers.get("content-type")
        if "content-length" in headers:
            env["CONTENT_LENGTH"] = headers.get("content-length")
            body = client.recv(int(env["CONTENT_LENGTH"]))
            env["wsgi.input"] = io.StringIO(body)
        else:
            body = client.recv(1024)
            env["wsgi.input"] = io.StringIO(body)
        for name, value in headers.items():
            key = "HTTP_" + name.replace("-", "_").upper()
            if key in env:
                value = "{0},{1}".format(env[key], value)
            env[key] = value

        return env

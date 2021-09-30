# SPDX-FileCopyrightText: 2019 Brent Rubell for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`wiznet5k_ntp`
================================================================================

Network Time Protocol (NTP) helper for CircuitPython

 * Author(s): irinakim

Implementation Notes
--------------------
**Hardware:**
**Software and Dependencies:**

 
"""
import time

import adafruit_wiznet5k.adafruit_wiznet5k_socket as socket
from adafruit_wiznet5k.adafruit_wiznet5k_socket import htons


##__version__ = "0.0.0-auto.0"
##__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_NTP.git"


class NTP:
    def __init__(self, iface, ntp_address,utc,debug=False):
        self._debug = debug
        self._iface = iface
        socket.set_interface(self._iface)
        self._sock = socket.socket(type=socket.SOCK_DGRAM)
        self._sock.settimeout(1)
        self._utc = utc

        self._ntp_server = ntp_address
        self._host = 0
        self._request_id = 0  # request identifier
        
        self._pkt_buf_ = bytearray()

    def _build_ntp_header(self,ip):
        self._pkt_buf_.append(0x23)

        for i in range(55):
            self._pkt_buf_.append(0x00)

    def get_time(self):
        self._build_ntp_header(self._ntp_server)     
        self._sock.bind((None,50001))
        self._sock.sendto(self._pkt_buf_,(self._ntp_server, 123))
        while True:
            data = self._sock.recv()
            if data: 
                sec = data[40:44]
                int_cal = int.from_bytes(sec,"big")
                cal =int_cal - 2208988800 + self._utc *3600
                cal = time.localtime(cal) 
                return cal

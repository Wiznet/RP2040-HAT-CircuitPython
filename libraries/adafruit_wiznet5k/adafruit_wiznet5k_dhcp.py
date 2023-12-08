# SPDX-FileCopyrightText: 2009 Jordan Terrell (blog.jordanterrell.com)
# SPDX-FileCopyrightText: 2020 Brent Rubell for Adafruit Industries
# SPDX-FileCopyrightText: 2021 Patrick Van Oosterwijck @ Silicognition LLC
# SPDX-FileCopyrightText: 2022 Martin Stephens
#
# SPDX-License-Identifier: MIT

"""
`adafruit_wiznet5k_dhcp`
================================================================================

Pure-Python implementation of Jordan Terrell's DHCP library v0.3

* Author(s): Jordan Terrell, Brent Rubell, Martin Stephens

"""
from __future__ import annotations

try:
    from typing import TYPE_CHECKING, Optional, Union, Tuple

    if TYPE_CHECKING:
        from adafruit_wiznet5k.adafruit_wiznet5k import WIZNET5K
except ImportError:
    pass


import gc
import time
from random import randint
from micropython import const
from adafruit_wiznet5k.adafruit_wiznet5k_debug import (  # pylint: disable=ungrouped-imports
    debug_msg,
)

# DHCP State Machine
_STATE_INIT = const(0x01)
_STATE_SELECTING = const(0x02)
_STATE_REQUESTING = const(0x03)
_STATE_BOUND = const(0x04)
_STATE_RENEWING = const(0x05)
_STATE_REBINDING = const(0x06)

# DHCP Message Types
_DHCP_DISCOVER = const(1)
_DHCP_OFFER = const(2)
_DHCP_REQUEST = const(3)
_DHCP_DECLINE = const(4)
_DHCP_ACK = const(5)
_DHCP_NAK = const(6)
_DHCP_RELEASE = const(7)
_DHCP_INFORM = const(8)

# DHCP Message OP Codes
_DHCP_BOOT_REQUEST = const(0x01)
_DHCP_BOOT_REPLY = const(0x02)

_DHCP_HTYPE10MB = const(0x01)
_DHCP_HTYPE100MB = const(0x02)

_DHCP_HLENETHERNET = const(0x06)
_DHCP_HOPS = const(0x00)

_MAGIC_COOKIE = b"c\x82Sc"  # Four bytes 99.130.83.99
_MAX_DHCP_OPT = const(0x10)

_SNMR_UDP = const(0x02)

# Default DHCP Server port
_DHCP_SERVER_PORT = const(67)
# DHCP Lease Time, in seconds
_BROADCAST_SERVER_ADDR = b"\xff\xff\xff\xff"  # (255.255.255.255)
_UNASSIGNED_IP_ADDR = b"\x00\x00\x00\x00"  # (0.0.0.0)

# DHCP Response Options
_MSG_TYPE = const(53)
_SUBNET_MASK = const(1)
_ROUTERS_ON_SUBNET = const(3)
_DNS_SERVERS = const(6)
_DHCP_SERVER_ID = const(54)
_T1_VAL = const(58)
_T2_VAL = const(59)
_LEASE_TIME = const(51)
_OPT_END = const(255)

# Packet buffer
_BUFF_LENGTH = 512
_BUFF = bytearray(_BUFF_LENGTH)


class DHCP:
    """Wiznet5k DHCP Client.

    Implements a DHCP client using a finite state machine (FSM). This allows the DHCP client
    to run in a non-blocking mode suitable for CircuitPython.

    The DHCP client obtains a lease and maintains it. The process of obtaining the initial
    lease is run in a blocking mode, as several messages must be exchanged with the DHCP
    server. Once the lease has been allocated, lease maintenance can be performed in
    non-blocking mode as nothing needs to be done until it is time to reallocate the
    lease. Renewing or rebinding is a simpler process which may be repeated periodically
    until successful. If the lease expires, the client attempts to obtain a new lease in
    blocking mode when the maintenance routine is run.

    These class methods are not designed to be called directly. They should be called via
    methods in the WIZNET5K class.

    Since DHCP uses UDP, messages may be lost. The DHCP protocol uses exponential backoff
    for retrying. Retries occur after 4, 8, and 16 +/- 1 seconds (the final retry is followed
    by a wait of 32 seconds) so it takes about a minute to decide that no DHCP server
    is available.

    The DHCP client cannot check whether the allocated IP address is already in use because
    the ARP protocol is not available. Therefore, it is possible that the IP address
    allocated by the server has been manually assigned to another device. In most cases,
    the DHCP server will make this check before allocating an address, but some do not.

    The DHCPRELEASE message is not implemented. The DHCP protocol does not require it and
    DHCP servers can handle disappearing clients and clients that ask for 'replacement'
    IP addresses.
    """

    # pylint: disable=too-many-arguments, too-many-instance-attributes, invalid-name
    def __init__(
        self,
        eth: WIZNET5K,
        mac_address: bytes,
        hostname: Optional[str] = None,
        debug: bool = False,
    ) -> None:
        """
        :param adafruit_wiznet5k.WIZNET5K eth: Wiznet 5k object
        :param bytes mac_address: Hardware MAC address.
        :param Optional[str] hostname: The desired hostname, with optional {} to fill
            in the MAC address, defaults to None.
        :param bool debug: Enable debugging output.
        """
        self._debug = debug
        debug_msg("Initialising DHCP client instance.", self._debug)

        if not isinstance(mac_address, bytes):
            raise TypeError("MAC address must be a bytes object.")
        # Prevent buffer overrun in send_dhcp_message()
        if len(mac_address) != 6:
            raise ValueError("MAC address must be 6 bytes.")
        self._mac_address = mac_address

        # Set socket interface
        self._eth = eth

        # DHCP state machine
        self._dhcp_state = _STATE_INIT
        self._transaction_id = randint(1, 0x7FFFFFFF)
        self._start_time = 0.0
        self._blocking = False
        self._renew = None

        # DHCP binding configuration
        self.dhcp_server_ip = _BROADCAST_SERVER_ADDR
        self.local_ip = _UNASSIGNED_IP_ADDR
        self.gateway_ip = _UNASSIGNED_IP_ADDR
        self.subnet_mask = _UNASSIGNED_IP_ADDR
        self.dns_server_ip = _UNASSIGNED_IP_ADDR

        # Lease expiry times
        self._t1 = 0
        self._t2 = 0
        self._lease = 0

        # Host name
        mac_string = "".join("{:02X}".format(o) for o in mac_address)
        self._hostname = bytes(
            (hostname or "WIZnet{}").split(".")[0].format(mac_string)[:42], "utf-8"
        )

    def request_dhcp_lease(self) -> bool:
        """
        Request acquire a DHCP lease.

        :returns bool: A lease has been acquired.
        """
        debug_msg("Requesting DHCP lease.", self._debug)
        self._dhcp_state_machine(blocking=True)
        return self._dhcp_state == _STATE_BOUND

    def maintain_dhcp_lease(self, blocking: bool = False) -> None:
        """
        Maintain a DHCP lease.
        :param bool blocking: Run the DHCP FSM in non-blocking mode.
        """
        debug_msg("Maintaining lease with blocking = {}".format(blocking), self._debug)
        self._dhcp_state_machine(blocking=blocking)

    def _dsm_reset(self) -> None:
        """Close the socket and set attributes to default values used by the
        state machine INIT state."""
        debug_msg("Resetting DHCP state machine.", self._debug)
        self.dhcp_server_ip = _BROADCAST_SERVER_ADDR
        self._eth.ifconfig = (
            _UNASSIGNED_IP_ADDR,
            _UNASSIGNED_IP_ADDR,
            _UNASSIGNED_IP_ADDR,
            _UNASSIGNED_IP_ADDR,
        )
        self.gateway_ip = _UNASSIGNED_IP_ADDR
        self.local_ip = _UNASSIGNED_IP_ADDR
        self.subnet_mask = _UNASSIGNED_IP_ADDR
        self.dns_server_ip = _UNASSIGNED_IP_ADDR
        self._renew = None
        self._increment_transaction_id()
        self._start_time = time.monotonic()

    def _increment_transaction_id(self) -> None:
        """Increment the transaction ID and roll over from 0x7fffffff to 0."""
        debug_msg("Incrementing transaction ID", self._debug)
        self._transaction_id = (self._transaction_id + 1) & 0x7FFFFFFF

    def _next_retry_time(self, *, attempt: int, interval: int = 4) -> float:
        """Calculate a retry stop time.

        The interval is calculated as an exponential fallback with a random variation to
        prevent DHCP packet collisions. This timeout is intended to be compared with
        time.monotonic().

        :param int attempt: The current attempt, used as the exponent for calculating the
            timeout.
        :param int interval: The base retry interval in seconds. Defaults to 4 as per the
            DHCP standard for Ethernet connections. Minimum value 2, defaults to 4.

        :returns float: The timeout in time.monotonic() seconds.

        :raises ValueError: If the interval is not > 1 second as this could return a zero or
            negative delay.
        """
        debug_msg("Calculating next retry time and incrementing retries.", self._debug)
        if interval <= 1:
            raise ValueError("Retry interval must be > 1 second.")
        delay = 2**attempt * interval + randint(-1, 1) + time.monotonic()
        return delay

    def _receive_dhcp_response(self, socket_num: int, timeout: float) -> int:
        """
        Receive data from the socket in response to a DHCP query.

        Reads data from the buffer until a viable minimum packet size has been
        received or the operation times out. If a viable packet is received, it is
        stored in the global buffer and the number of bytes received is returned.
        If the packet is too short, it is discarded and zero is returned. The
        maximum packet size is limited by the size of the global buffer.

        :param int socket_num: Socket to read from.
        :param float timeout: time.monotonic at which attempt should time out.

        :returns int: The number of bytes stored in the global buffer.
        """
        debug_msg("Receiving a DHCP response.", self._debug)
        while time.monotonic() < timeout:
            # DHCP returns the query plus additional data. The query length is 236 bytes.
            if self._eth.socket_available(socket_num, _SNMR_UDP) > 236:
                bytes_count, bytes_read = self._eth.read_udp(socket_num, _BUFF_LENGTH)
                _BUFF[:bytes_count] = bytes_read
                debug_msg("Received {} bytes".format(bytes_count), self._debug)
                del bytes_read
                gc.collect()
                return bytes_count
        return 0  # No bytes received.

    def _process_messaging_states(self, *, message_type: int):
        """
        Process a message while the FSM is in SELECTING or REQUESTING state.

        Check the message and update the FSM state if it is a valid type.

        :param int message_type: The type of message received from the DHCP server.

        :returns bool: True if the message was valid for the current state.
        """
        if self._dhcp_state == _STATE_SELECTING and message_type == _DHCP_OFFER:
            debug_msg("FSM state is SELECTING with valid OFFER.", self._debug)
            self._dhcp_state = _STATE_REQUESTING
        elif self._dhcp_state == _STATE_REQUESTING:
            debug_msg("FSM state is REQUESTING.", self._debug)
            if message_type == _DHCP_NAK:
                debug_msg("Message is NAK, setting FSM state to INIT.", self._debug)
                self._dhcp_state = _STATE_INIT
            elif message_type == _DHCP_ACK:
                debug_msg("Message is ACK, setting FSM state to BOUND.", self._debug)
                self._t1 = self._start_time + self._lease // 2
                self._t2 = self._start_time + self._lease - self._lease // 8
                self._lease += self._start_time
                self._increment_transaction_id()
                if not self._renew:
                    self._eth.ifconfig = (
                        self.local_ip,
                        self.subnet_mask,
                        self.gateway_ip,
                        self.dns_server_ip,
                    )
                self._renew = None
                self._dhcp_state = _STATE_BOUND

    def _handle_dhcp_message(self) -> int:
        """Send, receive and process DHCP message. Update the finite state machine (FSM).

        Send a message and wait for a response from the DHCP server, resending on an
        exponential fallback schedule matching the DHCP standard if no response is received.
        Only called when the FSM is in SELECTING or REQUESTING states.

        :returns int: The DHCP message type, or 0 if no message received in non-blocking
            or renewing states.

        :raises ValueError: If the function is not called from SELECTING or BLOCKING FSM
            states.
        :raises TimeoutError: If the FSM is in blocking mode and no valid response has
            been received before the timeout expires.
        """
        # pylint: disable=too-many-branches
        debug_msg("Processing SELECTING or REQUESTING state.", self._debug)
        if self._dhcp_state == _STATE_SELECTING:
            msg_type_out = _DHCP_DISCOVER
        elif self._dhcp_state == _STATE_REQUESTING:
            msg_type_out = _DHCP_REQUEST
        else:
            raise ValueError(
                "FSM can only send messages while in SELECTING or REQUESTING states."
            )
        debug_msg("Setting up connection for DHCP.", self._debug)
        if self._renew:
            dhcp_server = self.dhcp_server_ip
        else:
            dhcp_server = _BROADCAST_SERVER_ADDR
        sock_num = None
        deadline = time.monotonic() + 5.0
        try:
            while sock_num is None:
                sock_num = self._eth.get_socket()
                if sock_num == 0xFF:
                    sock_num = None
                if time.monotonic() > deadline:
                    raise RuntimeError("Unable to initialize UDP socket.")

            self._eth.src_port = 68
            self._eth.socket_connect(
                sock_num, dhcp_server, _DHCP_SERVER_PORT, conn_mode=0x02
            )
            self._eth.src_port = 0

            message_length = self._generate_dhcp_message(message_type=msg_type_out)
            for attempt in range(4):  # Initial attempt plus 3 retries.
                self._eth.socket_write(sock_num, _BUFF[:message_length])
                next_resend = self._next_retry_time(attempt=attempt)
                while time.monotonic() < next_resend:
                    if self._receive_dhcp_response(sock_num, next_resend):
                        try:
                            msg_type_in = self._parse_dhcp_response()
                            debug_msg(
                                "Received message type {}".format(msg_type_in),
                                self._debug,
                            )
                            return msg_type_in
                        except ValueError as error:
                            debug_msg(error, self._debug)
                    if not self._blocking or self._renew:
                        debug_msg(
                            "No message, FSM is nonblocking or renewing, exiting loop.",
                            self._debug,
                        )
                        return 0  # Did not receive a response in a single attempt.
            raise TimeoutError(
                "No response from DHCP server after {} retries.".format(attempt)
            )
        finally:
            self._eth.socket_close(sock_num)  # Close the socket whatever happens.

    def _dhcp_state_machine(self, *, blocking: bool = False) -> None:
        """
        A finite state machine to allow the DHCP lease to be managed without blocking
        the main program. The initial lease...
        """
        debug_msg("DHCP FSM called with blocking = {}".format(blocking), self._debug)
        debug_msg("FSM initial state is {}".format(self._dhcp_state), self._debug)
        self._blocking = blocking
        while True:
            if self._dhcp_state == _STATE_BOUND:
                now = time.monotonic()
                if now < self._t1:
                    debug_msg("No timers have expired. Exiting FSM.", self._debug)
                    return
                if now > self._lease:
                    debug_msg(
                        "Lease has expired, switching state to INIT.", self._debug
                    )
                    self._blocking = True
                    self._dhcp_state = _STATE_INIT
                elif now > self._t2:
                    debug_msg(
                        "T2 has expired, switching state to REBINDING.", self._debug
                    )
                    self._dhcp_state = _STATE_REBINDING
                else:
                    debug_msg(
                        "T1 has expired, switching state to RENEWING.", self._debug
                    )
                    self._dhcp_state = _STATE_RENEWING

            if self._dhcp_state == _STATE_RENEWING:
                debug_msg("FSM state is RENEWING.", self._debug)
                self._renew = "renew"
                self._start_time = time.monotonic()
                self._dhcp_state = _STATE_REQUESTING

            if self._dhcp_state == _STATE_REBINDING:
                debug_msg("FSM state is REBINDING.", self._debug)
                self._renew = "rebind"
                self.dhcp_server_ip = _BROADCAST_SERVER_ADDR
                self._start_time = time.monotonic()
                self._dhcp_state = _STATE_REQUESTING

            if self._dhcp_state == _STATE_INIT:
                debug_msg("FSM state is INIT.", self._debug)
                self._dsm_reset()
                self._dhcp_state = _STATE_SELECTING

            if self._dhcp_state == _STATE_SELECTING:
                debug_msg("FSM state is SELECTING.", self._debug)
                self._process_messaging_states(message_type=self._handle_dhcp_message())

            if self._dhcp_state == _STATE_REQUESTING:
                debug_msg("FSM state is REQUESTING.", self._debug)
                self._process_messaging_states(message_type=self._handle_dhcp_message())

            if self._renew:
                debug_msg(
                    "Lease has not expired, resetting state to BOUND and exiting FSM.",
                    self._debug,
                )
                self._dhcp_state = _STATE_BOUND
                return
            gc.collect()

    def _generate_dhcp_message(
        self,
        *,
        message_type: int,
        broadcast: bool = False,
    ) -> int:
        """
        Assemble a DHCP message. The content will vary depending on which type of
            message is being sent and whether the lease is new or being renewed.

        :param int message_type: Type of message to generate.
        :param bool broadcast: Used to set the flag requiring a broadcast reply from the
            DHCP server. Defaults to False which matches the DHCP standard.

        :returns int: The length of the DHCP message.
        """

        def option_writer(
            offset: int, option_code: int, option_data: Union[Tuple[int, ...], bytes]
        ) -> int:
            """Helper function to set DHCP option data for a DHCP
            message.

            :param int offset: Pointer to start of a DHCP option.
            :param int option_code: Type of option to add.
            :param Tuple[int] option_data: The data for the option.

            :returns int: Pointer to start of next option.
            """
            _BUFF[offset] = option_code
            data_length = len(option_data)
            offset += 1
            _BUFF[offset] = data_length
            offset += 1
            data_end = offset + data_length
            _BUFF[offset:data_end] = bytes(option_data)
            return data_end

        debug_msg("Generating DHCP message type {}".format(message_type), self._debug)
        # global _BUFF  # pylint: disable=global-variable-not-assigned
        _BUFF[:] = bytearray(_BUFF_LENGTH)
        # OP.HTYPE.HLEN.HOPS
        _BUFF[0:4] = bytes(
            [_DHCP_BOOT_REQUEST, _DHCP_HTYPE10MB, _DHCP_HLENETHERNET, _DHCP_HOPS]
        )
        # Transaction ID (xid)
        _BUFF[4:8] = self._transaction_id.to_bytes(4, "big")
        # Seconds elapsed
        _BUFF[8:10] = int(time.monotonic() - self._start_time).to_bytes(2, "big")
        # Flags (only bit 0 is used, all other bits must be 0)
        if broadcast:
            _BUFF[10] = 0b10000000
        else:
            _BUFF[10] = 0b00000000
        if self._renew:
            _BUFF[12:16] = bytes(self.local_ip)
        # chaddr
        _BUFF[28:34] = self._mac_address
        # Magic Cookie
        _BUFF[236:240] = _MAGIC_COOKIE

        # Set DHCP options.
        pointer = 240

        # Option - DHCP Message Type
        pointer = option_writer(
            offset=pointer, option_code=53, option_data=(message_type,)
        )
        # Option - Host Name
        pointer = option_writer(
            offset=pointer, option_code=12, option_data=self._hostname
        )

        # Option - Client ID
        pointer = option_writer(
            offset=pointer,
            option_code=61,
            option_data=b"\x01" + self._mac_address,
        )

        # Request subnet mask, router and DNS server.
        pointer = option_writer(offset=pointer, option_code=55, option_data=(1, 3, 6))

        # Request a 90 day lease.
        pointer = option_writer(
            offset=pointer, option_code=51, option_data=b"\x00\x76\xa7\x00"
        )

        if message_type == _DHCP_REQUEST:
            # Set Requested IP Address to offered IP address.
            pointer = option_writer(
                offset=pointer, option_code=50, option_data=self.local_ip
            )
            # Set Server ID to chosen DHCP server IP address.
            if self._renew != "rebind":
                pointer = option_writer(
                    offset=pointer, option_code=54, option_data=self.dhcp_server_ip
                )

        _BUFF[pointer] = 0xFF
        pointer += 1
        if pointer > _BUFF_LENGTH:
            raise ValueError("DHCP message too long.")
        debug_msg(_BUFF[:pointer], self._debug)
        return pointer

    def _parse_dhcp_response(
        self,
    ) -> int:
        """Parse DHCP response from DHCP server.

        Check that the message is for this client. Extract data from the fixed positions
        in the first 236 bytes of the message, then cycle through the options for
        additional data.

        :returns Tuple[int, bytearray]: DHCP packet type and ID.

        :raises ValueError: Checks that the message is a reply, the transaction ID
            matches, a client ID exists and the 'magic cookie' is set. If any of these tests
            fail or no message type is found in the options, raises a ValueError.
        """

        # pylint: disable=too-many-branches
        def option_reader(pointer: int) -> Tuple[int, int, bytes]:
            """Helper function to extract DHCP option data from a
            response.

            :param int pointer: Pointer to start of a DHCP option.

            :returns Tuple[int, int, bytes]: Pointer to next option,
                option type, and option data.
            """
            # debug_msg("initial pointer = {}".format(pointer), self._debug)
            option_type = _BUFF[pointer]
            # debug_msg("option type = {}".format(option_type), self._debug)
            pointer += 1
            data_length = _BUFF[pointer]
            # debug_msg("data length = {}".format(data_length), self._debug)
            pointer += 1
            data_end = pointer + data_length
            # debug_msg("data end = {}".format(data_end), self._debug)
            option_data = bytes(_BUFF[pointer:data_end])
            # debug_msg(option_data, self._debug)
            # debug_msg("Final pointer = {}".format(pointer), self._debug)
            return data_end, option_type, option_data

        debug_msg("Parsing DHCP message.", self._debug)
        # Validate OP
        if _BUFF[0] != _DHCP_BOOT_REPLY:
            raise ValueError("DHCP message is not the expected DHCP Reply.")
        # Confirm transaction IDs match.
        xid = _BUFF[4:8]
        if xid != self._transaction_id.to_bytes(4, "big"):
            raise ValueError("DHCP response ID mismatch.")
        # Check that there is a client ID.
        if _BUFF[28:34] == b"\x00\x00\x00\x00\x00\x00":
            raise ValueError("No client hardware MAC address in the response.")
        # Check for the magic cookie.
        if _BUFF[236:240] != _MAGIC_COOKIE:
            raise ValueError("No DHCP Magic Cookie in the response.")
        # Set the IP address to Claddr
        self.local_ip = bytes(_BUFF[16:20])

        # Parse options
        msg_type = None
        ptr = 240
        while _BUFF[ptr] != _OPT_END:
            ptr, data_type, data = option_reader(ptr)
            if data_type == _MSG_TYPE:
                msg_type = data[0]
            elif data_type == _SUBNET_MASK:
                self.subnet_mask = data
            elif data_type == _DHCP_SERVER_ID:
                self.dhcp_server_ip = data
            elif data_type == _LEASE_TIME:
                self._lease = int.from_bytes(data, "big")
            elif data_type == _ROUTERS_ON_SUBNET:
                self.gateway_ip = data[:4]
            elif data_type == _DNS_SERVERS:
                self.dns_server_ip = data[:4]
            elif data_type == _T1_VAL:
                self._t1 = int.from_bytes(data, "big")
            elif data_type == _T2_VAL:
                self._t2 = int.from_bytes(data, "big")
            elif data_type == 0:
                break

        debug_msg(
            "Msg Type: {}\nSubnet Mask: {}\nDHCP Server IP: {}\nDNS Server IP: {}\
                  \nGateway IP: {}\nLocal IP: {}\nT1: {}\nT2: {}\nLease Time: {}".format(
                msg_type,
                self.subnet_mask,
                self.dhcp_server_ip,
                self.dns_server_ip,
                self.gateway_ip,
                self.local_ip,
                self._t1,
                self._t2,
                self._lease,
            ),
            self._debug,
        )
        if msg_type is None:
            raise ValueError("No valid message type in response.")
        return msg_type

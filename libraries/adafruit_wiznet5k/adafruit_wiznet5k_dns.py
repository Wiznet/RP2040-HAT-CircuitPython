# SPDX-FileCopyrightText: 2009-2010 MCQN Ltd
# SPDX-FileCopyrightText: Brent Rubell for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_wiznet5k_dns`
================================================================================

Pure-Python implementation of the Arduino DNS client for WIZnet 5k-based
ethernet modules.

* Author(s): MCQN Ltd, Brent Rubell, Martin Stephens

"""
from __future__ import annotations

try:
    from typing import TYPE_CHECKING, Union, Tuple

    if TYPE_CHECKING:
        from adafruit_wiznet5k.adafruit_wiznet5k import WIZNET5K
except ImportError:
    pass

import time
from random import getrandbits
from micropython import const

_QUERY_FLAG = const(0x00)
_OPCODE_STANDARD_QUERY = const(0x00)
_RECURSION_DESIRED_FLAG = 1 << 8

_TYPE_A = const(0x0001)
_CLASS_IN = const(0x0001)
_DATA_LEN = const(0x0004)

# Return codes for gethostbyname
_SUCCESS = const(1)
_TIMED_OUT = const(-1)
_INVALID_SERVER = const(-2)
_TRUNCATED = const(-3)
_INVALID_RESPONSE = const(-4)

_DNS_PORT = const(0x35)  # port used for DNS request


def _debug_print(*, debug: bool, message: str) -> None:
    """Helper function to improve code readability."""
    if debug:
        print(message)


def _build_dns_query(domain: bytes) -> Tuple[int, int, bytearray]:
    """Builds DNS header."""
    # generate a random, 16-bit, request identifier
    query_id = getrandbits(16)
    # Hard code everything except the ID, it never changes in this implementation.
    query = bytearray(
        [
            query_id >> 8,  # Query MSB.
            query_id & 0xFF,  # Query LSB.
            0x01,  # Flags MSB: QR=0, 4 bit Opcode=0, AA=0, TC=0, RD=1 (recursion is desired).
            0x00,  # Flags LSB: RA=0, 3 bit Z=0, 4 bit RCode=0.
            0x00,  # QDcount MSB:
            0x01,  # QDcount LSB: Question count, always 1 in this implementation.
            0x00,  # ANcount MSB:
            0x00,  # ANcount LSB: Answer Record Count, 0 in queries.
            0x00,  # NScount MSB:
            0x00,  # NScount LSB: Authority Record Count, 0 in queries.
            0x00,  # ARcount MSB:
            0x00,  # ARcount LSB: Additional Record Count, 0 in queries.
        ]
    )
    host = domain.decode("utf-8").split(".")
    # Write out each label of question name.
    for label in host:
        # Append the length of the label
        query.append(len(label))
        # Append the label
        query += bytes(label, "utf-8")
    # Hard code null, question type and class as they never vary.
    query += bytearray(
        [
            0x00,  # Null, indicates end of question name
            0x00,  # Question Type MSB:
            0x01,  # Question Type LSB: Always 1 (Type A) in this implementation.
            0x00,  # Question Class MSB:
            0x01,  # Question Class LSB: Always 1 (Class IN) in this implementation.
        ]
    )
    return query_id, len(query), query


def _parse_dns_response(
    *, response: bytearray, query_id: int, query_length: int, debug: bool
) -> bytearray:
    # pylint: disable=too-many-branches
    """
    Parses a DNS query response.

    :param bytearray response: Data returned as a DNS query response.
    :param int query_id: The ID of the query that generated the response, used to validate
        the response.
    :param int query_length: The number of bytes in the DNS query that generated the response.
    :param bool debug: Whether to output debugging messsages.

    :returns bytearray: Four byte IPv4 address.

    :raises ValueError: If the response does not yield a valid IPv4 address from a type A,
        class IN answer.
    """
    # Validate request identifier
    response_id = int.from_bytes(response[0:2], "big")
    _debug_print(
        debug=debug, message="Parsing packet with ID {x:#x}".format(x=response_id)
    )
    if response_id != query_id:
        raise ValueError(
            "Response ID 0x{x:x} does not match query ID 0x{y:x}".format(
                x=response_id, y=query_id
            )
        )
    # Validate flags
    flags = int.from_bytes(response[2:4], "big")
    # Mask out authenticated, truncated and recursion bits, unimportant to parsing.
    flags &= 0xF87F
    # Check that the response bit is set, the query is standard and no error occurred.
    if flags != 0x8000:
        # noinspection PyStringFormat
        raise ValueError("Invalid flags {x:#04x}, {x:#016b}.".format(x=flags))
    # Number of questions
    question_count = int.from_bytes(response[4:6], "big")
    # Never more than one question per DNS query in this implementation.
    if question_count != 1:
        raise ValueError("Question count should be 1, is {}.".format(question_count))
    # Number of answers
    answer_count = int.from_bytes(response[6:8], "big")
    _debug_print(debug=debug, message="* DNS Answer Count: {}.".format(answer_count))
    if answer_count < 1:
        raise ValueError("Answer count should be > 0, is {}.".format(answer_count))

    # Parse answers
    pointer = query_length  # Response header is the same length as the query header.
    # pylint: disable=too-many-nested-blocks
    try:
        for answer in range(answer_count):
            # Move the pointer past the name.
            label_length = response[pointer]
            while True:
                if label_length >= 0xC0:
                    # Pointer to a section of domain name, skip over it.
                    pointer += 2
                    label_length = response[pointer]
                    if label_length == 0:
                        # One byte past the end of the name.
                        break
                else:
                    # Section of the domain name, skip through it.
                    pointer += label_length
                    label_length = response[pointer]
                    if label_length == 0:
                        # On the null byte at the end of the name. Increment the pointer.
                        pointer += 1
                        break
            # Check for a type A answer.
            if int.from_bytes(response[pointer : pointer + 2], "big") == _TYPE_A:
                # Check for an IN class answer.
                if (
                    int.from_bytes(response[pointer + 2 : pointer + 4], "big")
                    == _CLASS_IN
                ):
                    _debug_print(
                        debug=debug,
                        message="Type A, class IN found in answer {x} of {y}.".format(
                            x=answer + 1, y=answer_count
                        ),
                    )
                    # Set pointer to start of resource record.
                    pointer += 8
                    # Confirm that the resource record is 4 bytes (an IPv4 address).
                    if (
                        int.from_bytes(response[pointer : pointer + 2], "big")
                        == _DATA_LEN
                    ):
                        ipv4 = response[pointer + 2 : pointer + 6]
                        # Low probability that the response was truncated inside the 4 byte address.
                        if len(ipv4) != _DATA_LEN:
                            raise ValueError("IPv4 address is not 4 bytes.")
                        _debug_print(
                            debug=debug,
                            message="IPv4 address found : 0x{:x}.".format(
                                int.from_bytes(ipv4, "big")
                            ),
                        )
                        return ipv4
            # Set pointer to start of next answer
            pointer += 10 + int.from_bytes(response[pointer + 8 : pointer + 10], "big")
            _debug_print(
                debug=debug,
                message="Answer {x} of {y} was not type A, class IN.".format(
                    x=answer + 1, y=answer_count
                ),
            )
        # No IPv4 address in any answer.
        raise ValueError()
    except (IndexError, ValueError) as error:
        # IndexError means we ran out of data in an answer, maybe truncated.
        # ValueError means we ran out of answers.
        raise ValueError(
            "No type A, class IN answers found in the DNS response."
        ) from error


class DNS:
    """W5K DNS implementation."""

    def __init__(
        self,
        iface: WIZNET5K,
        dns_address: Union[str, Tuple[int, int, int, int]],
        debug: bool = False,
    ) -> None:
        """
        :param adafruit_wiznet5k.WIZNET5K: Ethernet network connection.
        :param Union[str, Tuple[int, int, int, int]]: IP address of the DNS server.
        :param bool debug: Enable debugging messages, defaults to False.
        """
        self._debug = debug
        self._iface = iface
        self._dns_server = (
            self._iface.unpretty_ip(dns_address)
            if isinstance(dns_address, str)
            else dns_address
        )
        self._query_id = 0  # Request ID.
        self._query_length = 0  # Length of last query.

    def gethostbyname(self, hostname: bytes) -> Union[int, bytes]:
        """
        DNS look up of a host name.

        :param bytes hostname: Host name to connect to.

        :return Union[int, bytes] The IPv4 address if successful, -1 otherwise.
        """
        if self._dns_server is None:
            return _INVALID_SERVER
        # build DNS request packet
        self._query_id, self._query_length, buffer = _build_dns_query(hostname)

        # Send DNS request packet
        dns_socket = self._iface.get_socket()
        self._iface.socket_connect(
            dns_socket, bytes(self._dns_server), _DNS_PORT, conn_mode=0x02
        )
        _debug_print(debug=self._debug, message="* DNS: Sending request packet...")
        self._iface.socket_write(dns_socket, buffer)

        # Read and parse the DNS response
        ipaddress = -1
        for _ in range(5):
            #  wait for a response
            socket_timeout = time.monotonic() + 5.0
            while not self._iface.socket_available(dns_socket, 0x02):
                if time.monotonic() > socket_timeout:
                    _debug_print(
                        debug=self._debug,
                        message="* DNS ERROR: Did not receive DNS response (socket timeout).",
                    )
                    self._iface.socket_close(dns_socket)
                    raise RuntimeError("Failed to resolve hostname!")
                time.sleep(0.05)
            # recv packet into buf
            _, buffer = self._iface.read_udp(dns_socket, 512)
            _debug_print(
                debug=self._debug,
                message="DNS Packet Received: {}".format(buffer),
            )
            try:
                ipaddress = _parse_dns_response(
                    response=buffer,
                    query_id=self._query_id,
                    query_length=self._query_length,
                    debug=self._debug,
                )
                break
            except ValueError as error:
                _debug_print(
                    debug=self._debug,
                    message="* DNS ERROR: Failed to resolve DNS response, retrying…\n"
                    "    ({}).".format(error.args[0]),
                )
        self._iface.socket_close(dns_socket)
        return ipaddress

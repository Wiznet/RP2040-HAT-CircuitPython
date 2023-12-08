# SPDX-FileCopyrightText: 2010 WIZnet
# SPDX-FileCopyrightText: 2010 Arduino LLC
# SPDX-FileCopyrightText: 2008 Bjoern Hartmann
# SPDX-FileCopyrightText: 2018 Paul Stoffregen
# SPDX-FileCopyrightText: 2020 Brent Rubell for Adafruit Industries
# SPDX-FileCopyrightText: 2021 Patrick Van Oosterwijck
# SPDX-FileCopyrightText: 2021 Adam Cummick
# SPDX-FileCopyrightText: 2023 Martin Stephens
#
# SPDX-License-Identifier: MIT
"""
`adafruit_wiznet5k`
================================================================================

Pure-Python interface for WIZNET 5k ethernet modules.

* Author(s): WIZnet, Arduino LLC, Bjoern Hartmann, Paul Stoffregen, Brent Rubell,
  Patrick Van Oosterwijck, Martin Stephens

Implementation Notes
--------------------

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://github.com/adafruit/circuitpython/releases

* Adafruit's Bus Device library: https://github.com/adafruit/Adafruit_CircuitPython_BusDevice
"""

# pylint: disable=too-many-lines
from __future__ import annotations

try:
    from typing import TYPE_CHECKING, Optional, Union, Tuple

    if TYPE_CHECKING:
        from circuitpython_typing import WriteableBuffer
        import busio
        import digitalio

        IpAddress4Raw = Union[bytes, Tuple[int, int, int, int]]
        MacAddressRaw = Union[bytes, Tuple[int, int, int, int, int, int]]
except ImportError:
    pass

__version__ = "0.0.0+auto.0"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_Wiznet5k.git"

from random import randint
import time
import gc
from micropython import const

from adafruit_bus_device.spi_device import SPIDevice
import adafruit_wiznet5k.adafruit_wiznet5k_dhcp as dhcp
import adafruit_wiznet5k.adafruit_wiznet5k_dns as dns
from adafruit_wiznet5k.adafruit_wiznet5k_debug import debug_msg

# *** Wiznet Common Registers ***
_REG_MR = {"w5100s": const(0x0000), "w5500": const(0x0000)}
# Gateway IPv4 Address.
_REG_GAR = {"w5100s": const(0x0001), "w5500": const(0x0001), "w6100": const(0x4130)}
# Subnet Mask Address
_REG_SUBR = {"w5100s": const(0x0005), "w5500": const(0x0005), "w6100": const(0x4134)}
# Chip version.
_REG_VERSIONR = {
    "w5100s": const(0x0080),
    "w5500": const(0x0039),
    "w6100": const(0x0000),
}
# Source Hardware Address
_REG_SHAR = {"w5100s": const(0x0009), "w5500": const(0x0009), "w6100": const(0x4120)}
# Source IP Address
_REG_SIPR = {"w5100s": const(0x000F), "w5500": const(0x000F), "w6100": const(0x4138)}
# Register with link status flag (PHYCFGR for 5xxxx, PHYSR for 6100).
_REG_LINK_FLAG = {
    "w5100s": const(0x003C),
    "w5500": const(0x002E),
    "w6100": const(0x3000),
}
_REG_RCR = {"w5100s": const(0x0019), "w5500": const(0x001B), "w6100": const(0x4204)}
_REG_RTR = {"w5100s": const(0x0017), "w5500": const(0x0019), "w6100": const(0x4200)}

# *** Wiznet Socket Registers ***
# Socket n Mode.
_REG_SNMR = const(0x0000)
# Socket n Command.
_REG_SNCR = {"w5100s": const(0x0001), "w5500": const(0x0001), "w6100": const(0x0010)}
# Socket n Interrupt.
_REG_SNIR = {"w5100s": const(0x0002), "w5500": const(0x0002), "w6100": const(0x0020)}
# Socket n Status.
_REG_SNSR = {"w5100s": const(0x0003), "w5500": const(0x0003), "w6100": const(0x0030)}
# Socket n Source Port.
_REG_SNPORT = {"w5100s": const(0x0004), "w5500": const(0x0004), "w6100": const(0x0114)}
# Destination IPv4 Address.
_REG_SNDIPR = {"w5100s": const(0x000C), "w5500": const(0x000C), "w6100": const(0x0120)}
# Destination Port.
_REG_SNDPORT = {"w5100s": const(0x0010), "w5500": const(0x0010), "w6100": const(0x0140)}
# RX Free Size.
_REG_SNRX_RSR = {
    "w5100s": const(0x0026),
    "w5500": const(0x0026),
    "w6100": const(0x0224),
}
# Read Size Pointer.
_REG_SNRX_RD = {"w5100s": const(0x0028), "w5500": const(0x0028), "w6100": const(0x0228)}
# Socket n TX Free Size.
_REG_SNTX_FSR = {
    "w5100s": const(0x0020),
    "w5500": const(0x0020),
    "w6100": const(0x0204),
}
# TX Write Pointer.
_REG_SNTX_WR = {"w5100s": const(0x0024), "w5500": const(0x0024), "w6100": const(0x020C)}

# SNSR Commands
SNSR_SOCK_CLOSED = const(0x00)
_SNSR_SOCK_INIT = const(0x13)
SNSR_SOCK_LISTEN = const(0x14)
_SNSR_SOCK_SYNSENT = const(0x15)
SNSR_SOCK_SYNRECV = const(0x16)
SNSR_SOCK_ESTABLISHED = const(0x17)
SNSR_SOCK_FIN_WAIT = const(0x18)
_SNSR_SOCK_CLOSING = const(0x1A)
SNSR_SOCK_TIME_WAIT = const(0x1B)
SNSR_SOCK_CLOSE_WAIT = const(0x1C)
_SNSR_SOCK_LAST_ACK = const(0x1D)
_SNSR_SOCK_UDP = const(0x22)
_SNSR_SOCK_IPRAW = const(0x32)
_SNSR_SOCK_MACRAW = const(0x42)
_SNSR_SOCK_PPPOE = const(0x5F)

# Sock Commands (CMD)
_CMD_SOCK_OPEN = const(0x01)
_CMD_SOCK_LISTEN = const(0x02)
_CMD_SOCK_CONNECT = const(0x04)
_CMD_SOCK_DISCON = const(0x08)
_CMD_SOCK_CLOSE = const(0x10)
_CMD_SOCK_SEND = const(0x20)
_CMD_SOCK_SEND_MAC = const(0x21)
_CMD_SOCK_SEND_KEEP = const(0x22)
_CMD_SOCK_RECV = const(0x40)

# Socket n Interrupt Register
_SNIR_SEND_OK = const(0x10)
SNIR_TIMEOUT = const(0x08)
_SNIR_RECV = const(0x04)
SNIR_DISCON = const(0x02)
_SNIR_CON = const(0x01)

_CH_SIZE = const(0x100)
_SOCK_SIZE = const(0x800)  # MAX W5k socket size
_SOCK_MASK = const(0x7FF)
# Register commands
_MR_RST = const(0x80)  # Mode Register RST
# Socket mode register
_SNMR_CLOSE = const(0x00)
_SNMR_TCP = const(0x21)
SNMR_UDP = const(0x02)
_SNMR_IPRAW = const(0x03)
_SNMR_MACRAW = const(0x04)
_SNMR_PPPOE = const(0x05)

_MAX_PACKET = const(4000)
_LOCAL_PORT = const(0x400)
# Default hardware MAC address
_DEFAULT_MAC = (0xDE, 0xAD, 0xBE, 0xEF, 0xFE, 0xED)

# Maximum number of sockets to support, differs between chip versions.
_MAX_SOCK_NUM = {"w5100s": const(0x04), "w5500": const(0x08), "w6100": const(0x08)}
_SOCKET_INVALID = const(0xFF)


def _unprettyfy(data: str, seperator: str, correct_length: int) -> bytes:
    """Helper for converting . or : delimited strings to bytes objects."""
    data = bytes(int(x) for x in data.split(seperator))
    if len(data) == correct_length:
        return data
    raise ValueError("Invalid IP or MAC address.")


class WIZNET5K:  # pylint: disable=too-many-public-methods, too-many-instance-attributes
    """Interface for WIZNET5K module."""

    _TCP_MODE = const(0x21)
    _UDP_MODE = const(0x02)
    _TLS_MODE = const(0x03)  # This is NOT currently implemented

    _sockets_reserved = []

    # pylint: disable=too-many-arguments
    def __init__(
        self,
        spi_bus: busio.SPI,
        cs: digitalio.DigitalInOut,  # pylint: disable=invalid-name
        reset: Optional[digitalio.DigitalInOut] = None,
        is_dhcp: bool = True,
        mac: Union[MacAddressRaw, str] = _DEFAULT_MAC,
        hostname: Optional[str] = None,
        debug: bool = False,
    ) -> None:
        """
        :param busio.SPI spi_bus: The SPI bus the Wiznet module is connected to.
        :param digitalio.DigitalInOut cs: Chip select pin.
        :param digitalio.DigitalInOut reset: Optional reset pin, defaults to None.
        :param bool is_dhcp: Whether to start DHCP automatically or not, defaults to True.
        :param Union[MacAddressRaw, str] mac: The Wiznet's MAC Address, defaults to
            (0xDE, 0xAD, 0xBE, 0xEF, 0xFE, 0xED).
        :param str hostname: The desired hostname, with optional {} to fill in the MAC
            address, defaults to None.
        :param bool debug: Enable debugging output, defaults to False.
        """
        self._debug = debug
        self._chip_type = None
        self._device = SPIDevice(spi_bus, cs, baudrate=8000000, polarity=0, phase=0)
        # init c.s.
        self._cs = cs

        # Reset wiznet module prior to initialization.
        if reset:
            debug_msg("* Resetting WIZnet chip", self._debug)
            reset.switch_to_output()
            reset.value = False
            time.sleep(0.1)
            reset.value = True
            time.sleep(5)

        # Setup chip_select pin.
        time.sleep(1)
        self._cs.switch_to_output()
        self._cs.value = 1

        # Buffer for reading params from module
        self._pbuff = bytearray(8)
        self._rxbuf = bytearray(_MAX_PACKET)

        # attempt to initialize the module
        self._ch_base_msb = 0
        self._src_ports_in_use = []
        self._wiznet_chip_init()

        # Set MAC address
        self.mac_address = mac
        self.src_port = 0
        self._dns = b"\x00\x00\x00\x00"
        # udp related
        self.udp_from_ip = [b"\x00\x00\x00\x00"] * self.max_sockets
        self.udp_from_port = [0] * self.max_sockets

        # Wait to give the Ethernet link to initialise.
        stop_time = time.monotonic() + 5
        while time.monotonic() < stop_time:
            if self.link_status:
                break
            debug_msg("Ethernet link is down…", self._debug)
            time.sleep(0.5)
        self._dhcp_client = None

        # Set DHCP
        if is_dhcp:
            self.set_dhcp(hostname)

    def set_dhcp(self, hostname: Optional[str] = None) -> None:
        """
        Initialize the DHCP client and attempt to retrieve and set network
        configuration from the DHCP server.

        :param Optional[str] hostname: The desired hostname for the DHCP server with
            optional {} to fill in the MAC address, defaults to None.

        :raises RuntimeError: If DHCP lease cannot be established.
        """
        debug_msg("* Initializing DHCP", self._debug)
        self._dhcp_client = dhcp.DHCP(self, self.mac_address, hostname, self._debug)
        if self._dhcp_client.request_dhcp_lease():
            debug_msg(
                "Found DHCP Server:\nIP: {}\n  Subnet Mask: {}\n  GW Addr: {}"
                "\n  DNS Server: {}".format(*self.ifconfig),
                self._debug,
            )
        else:
            self._dhcp_client = None
            raise RuntimeError("Failed to configure DHCP Server!")

    def maintain_dhcp_lease(self) -> None:
        """Maintain the DHCP lease."""
        if self._dhcp_client:
            self._dhcp_client.maintain_dhcp_lease()

    def get_host_by_name(self, hostname: str) -> bytes:
        """
        Convert a hostname to a packed 4-byte IP Address.

        :param str hostname: The host name to be converted.

        :return bytes: The IPv4 address as a 4 byte array.

        :raises RuntimeError: If the DNS lookup fails.
        """
        debug_msg("Get host by name", self._debug)
        if isinstance(hostname, str):
            hostname = bytes(hostname, "utf-8")
        # Return IP assigned by DHCP
        _dns_client = dns.DNS(
            self, self.pretty_ip(bytearray(self._dns)), debug=self._debug
        )
        ipv4 = _dns_client.gethostbyname(hostname)
        debug_msg("* Resolved IP: {}".format(ipv4), self._debug)
        if ipv4 == -1:
            raise RuntimeError("Failed to resolve hostname!")
        return ipv4

    @property
    def max_sockets(self) -> int:
        """
        Maximum number of sockets supported by chip.

        :return int: Maximum supported sockets.
        """
        return _MAX_SOCK_NUM[self._chip_type]

    @property
    def chip(self) -> str:
        """
        Ethernet controller chip type.

        :return str: The chip type.
        """
        return self._chip_type

    @property
    def ip_address(self) -> bytes:
        """
        Configured IP address for the WIZnet Ethernet hardware.

        :return bytes: IP address as four bytes.
        """
        return self._read(_REG_SIPR[self._chip_type], 0x00, 4)

    @staticmethod
    def pretty_ip(ipv4: bytes) -> str:
        """
        Convert a 4 byte IP address to a dotted-quad string for printing.

        :param bytearray ipv4: A four byte IP address.

        :return str: The IP address (a string of the form '255.255.255.255').

        :raises ValueError: If IP address is not 4 bytes.
        """
        if len(ipv4) != 4:
            raise ValueError("Wrong length for IPv4 address.")
        return ".".join(f"{byte}" for byte in ipv4)

    @staticmethod
    def unpretty_ip(ipv4: str) -> bytes:
        """
        Convert a dotted-quad string to a four byte IP address.

        :param str ipv4: IPv4 address (a string of the form '255.255.255.255') to be converted.

        :return bytes: IPv4 address in four bytes.

        :raises ValueError: If IPv4 address is not 4 bytes.
        """
        return _unprettyfy(ipv4, ".", 4)

    @property
    def mac_address(self) -> bytes:
        """
        The WIZnet Ethernet hardware MAC address.

        :return bytes: Six byte MAC address.
        """
        return self._read(_REG_SHAR[self._chip_type], 0x00, 6)

    @mac_address.setter
    def mac_address(self, address: Union[MacAddressRaw, str]) -> None:
        """
        Set the WIZnet hardware MAC address.

        :param Union[MacAddressRaw, str] address: A hardware MAC address.

        :raises ValueError: If the MAC address is invalid
        """
        try:
            address = [int(x, 16) for x in address.split(":")]
        except AttributeError:
            pass
        try:
            if len(address) != 6:
                raise ValueError()
            # Bytes conversion will raise ValueError if values are not 0-255
            self._write(_REG_SHAR[self._chip_type], 0x04, bytes(address))
        except ValueError:
            # pylint: disable=raise-missing-from
            raise ValueError("Invalid MAC address.")

    @staticmethod
    def pretty_mac(mac: bytes) -> str:
        """
        Convert a bytes MAC address to a ':' seperated string for display.

        :param bytes mac: The MAC address.

        :return str: Mac Address in the form 00:00:00:00:00:00

        :raises ValueError: If MAC address is not 6 bytes.
        """
        if len(mac) != 6:
            raise ValueError("Incorrect length for MAC address.")
        return ":".join(f"{byte:02x}" for byte in mac)

    def remote_ip(self, socket_num: int) -> str:
        """
        IP address of the host which sent the current incoming packet.

        :param int socket_num: ID number of the socket to check.

        :return str: The IPv4 address.

        :raises ValueError: If the socket number is out of range.
        """
        self._sock_num_in_range(socket_num)
        for octet in range(4):
            self._pbuff[octet] = self._read_socket_register(
                socket_num, _REG_SNDIPR[self._chip_type] + octet
            )
        return self.pretty_ip(self._pbuff[:4])

    def remote_port(self, socket_num: int) -> int:
        """
        Port number of the host which sent the current incoming packet.

        :param int socket_num: ID number of the socket to check.

        :return int: The incoming port number of the socket connection.

        :raises ValueError: If the socket number is out of range.
        """
        self._sock_num_in_range(socket_num)
        return self._read_two_byte_sock_reg(socket_num, _REG_SNDPORT[self._chip_type])

    @property
    def link_status(self) -> bool:
        """
        Physical hardware (PHY) connection status.

        Whether the WIZnet hardware is physically connected to an Ethernet network.

        :return bool: True if the link is up, False if the link is down.
        """
        return bool(
            int.from_bytes(self._read(_REG_LINK_FLAG[self._chip_type], 0x00), "big")
            & 0x01
        )

    @property
    def ifconfig(self) -> Tuple[bytes, bytes, bytes, bytes]:
        """
        Network configuration information.

        :return Tuple[bytes, bytes, bytes, bytes]: The IP address, subnet mask, gateway
            address and DNS server address.
        """
        return (
            self.ip_address,
            self._read(_REG_SUBR[self._chip_type], 0x00, 4),
            self._read(_REG_GAR[self._chip_type], 0x00, 4),
            self._dns,
        )

    @ifconfig.setter
    def ifconfig(
        self, params: Tuple[IpAddress4Raw, IpAddress4Raw, IpAddress4Raw, IpAddress4Raw]
    ) -> None:
        """
        Set network configuration.

        :param Tuple[Address4Bytes, Address4Bytes, Address4Bytes, Address4Bytes]: Configuration
            settings - (ip_address, subnet_mask, gateway_address, dns_server).
        """
        for param in params:
            if len(param) != 4:
                raise ValueError("IPv4 address must be 4 bytes.")
        ip_address, subnet_mask, gateway_address, dns_server = params

        self._write(_REG_SIPR[self._chip_type], 0x04, bytes(ip_address))
        self._write(_REG_SUBR[self._chip_type], 0x04, bytes(subnet_mask))
        self._write(_REG_GAR[self._chip_type], 0x04, bytes(gateway_address))

        self._dns = bytes(dns_server)

    # *** Public Socket Methods ***

    def socket_available(self, socket_num: int, sock_type: int = _SNMR_TCP) -> int:
        """
        Number of bytes available to be read from the socket.

        :param int socket_num: Socket to check for available bytes.
        :param int sock_type: Socket type. Use SNMR_TCP for TCP or SNMR_UDP for UDP,
            defaults to SNMR_TCP.

        :return int: Number of bytes available to read.

        :raises ValueError: If the socket number is out of range.
        :raises ValueError: If the number of bytes on a UDP socket is negative.
        """
        debug_msg(
            "socket_available called on socket {}, protocol {}".format(
                socket_num, sock_type
            ),
            self._debug,
        )
        self._sock_num_in_range(socket_num)

        number_of_bytes = self._get_rx_rcv_size(socket_num)
        if self._read_snsr(socket_num) == SNMR_UDP:
            number_of_bytes -= 8  # Subtract UDP header from packet size.
        if number_of_bytes < 0:
            raise ValueError("Negative number of bytes found on socket.")
        return number_of_bytes

    def socket_status(self, socket_num: int) -> int:
        """
        Socket connection status.

        Can be: SNSR_SOCK_CLOSED, SNSR_SOCK_INIT, SNSR_SOCK_LISTEN, SNSR_SOCK_SYNSENT,
        SNSR_SOCK_SYNRECV, SNSR_SYN_SOCK_ESTABLISHED, SNSR_SOCK_FIN_WAIT,
        SNSR_SOCK_CLOSING, SNSR_SOCK_TIME_WAIT, SNSR_SOCK_CLOSE_WAIT, SNSR_LAST_ACK,
        SNSR_SOCK_UDP, SNSR_SOCK_IPRAW, SNSR_SOCK_MACRAW, SNSR_SOCK_PPOE.

        :param int socket_num: ID of socket to check.

        :return int: The connection status.
        """
        return self._read_snsr(socket_num)

    def socket_connect(
        self,
        socket_num: int,
        dest: IpAddress4Raw,
        port: int,
        conn_mode: int = _SNMR_TCP,
    ) -> int:
        """
        Open and verify a connection from a socket to a destination IPv4 address
        or hostname. A TCP connection is made by default. A UDP connection can also
        be made.

        :param int socket_num: ID of the socket to be connected.
        :param IpAddress4Raw dest: The destination as a host name or IP address.
        :param int port: Port to connect to (0 - 65,535).
        :param int conn_mode: The connection mode. Use SNMR_TCP for TCP or SNMR_UDP for UDP,
            defaults to SNMR_TCP.

        :raises ValueError: if the socket number is out of range.
        :raises ConnectionError: If the connection to the socket cannot be established.
        """
        self._sock_num_in_range(socket_num)
        self._check_link_status()
        debug_msg(
            "W5K socket connect, protocol={}, port={}, ip={}".format(
                conn_mode, port, self.pretty_ip(dest)
            ),
            self._debug,
        )
        # initialize a socket and set the mode
        self.socket_open(socket_num, conn_mode=conn_mode)
        # set socket destination IP and port
        self._write_sndipr(socket_num, dest)
        self._write_sndport(socket_num, port)
        self._write_sncr(socket_num, _CMD_SOCK_CONNECT)

        if conn_mode == _SNMR_TCP:
            # wait for tcp connection establishment
            while self.socket_status(socket_num) != SNSR_SOCK_ESTABLISHED:
                time.sleep(0.001)
                debug_msg(
                    "SNSR: {}".format(self.socket_status(socket_num)), self._debug
                )
                if self.socket_status(socket_num) == SNSR_SOCK_CLOSED:
                    raise ConnectionError("Failed to establish connection.")
        return 1

    def get_socket(self, *, reserve_socket=False) -> int:
        """
        Request, allocate and return a socket from the WIZnet 5k chip.

        Cycle through the sockets to find the first available one. If the called with
        reserve_socket=True, update the list of reserved sockets (intended to be used with
        socket.socket()). Note that reserved sockets must be released by calling
        release_socket() once they are no longer needed.

        If all sockets are reserved, no sockets are available for DNS calls, etc. Therefore,
        one socket cannot be reserved. Since socket 0 is the only socket that is capable of
        operating in MacRAW mode, it is the non-reservable socket.

        :param bool reserve_socket: Whether to reserve the socket.

        :returns int: The first available socket.

        :raises RuntimeError: If no socket is available.
        """
        debug_msg("*** Get socket.", self._debug)
        # Prefer socket zero for none reserved calls as it cannot be reserved.
        if not reserve_socket and self.socket_status(0) == SNSR_SOCK_CLOSED:
            debug_msg("Allocated socket # 0", self._debug)
            return 0
        # Then check the other sockets.

        #  Call garbage collection to encourage socket.__del__() be called to on any
        #  destroyed instances. Not at all guaranteed to work!
        gc.collect()
        debug_msg(
            "Reserved sockets: {}".format(WIZNET5K._sockets_reserved), self._debug
        )

        for socket_number, reserved in enumerate(WIZNET5K._sockets_reserved, start=1):
            if not reserved and self.socket_status(socket_number) == SNSR_SOCK_CLOSED:
                if reserve_socket:
                    WIZNET5K._sockets_reserved[socket_number - 1] = True
                    debug_msg(
                        "Allocated socket # {}.".format(socket_number),
                        self._debug,
                    )
                return socket_number
        raise RuntimeError("All sockets in use.")

    def release_socket(self, socket_number):
        """
        Update the socket reservation list when a socket is no longer reserved.

        :param int socket_number: The socket to release.

        :raises ValueError: If the socket number is out of range.
        """
        self._sock_num_in_range(socket_number)
        WIZNET5K._sockets_reserved[socket_number - 1] = False

    def socket_listen(
        self, socket_num: int, port: int, conn_mode: int = _SNMR_TCP
    ) -> None:
        """
        Listen on a socket's port.

        :param int socket_num: ID of socket to listen on.
        :param int port: Port to listen on (0 - 65,535).
        :param int conn_mode: Connection mode SNMR_TCP for TCP or SNMR_UDP for
            UDP, defaults to SNMR_TCP.

        :raises ValueError: If the socket number is out of range.
        :raises ConnectionError: If the Ethernet link is down.
        :raises RuntimeError: If unable to connect to a hardware socket.
        """
        self._sock_num_in_range(socket_num)
        self._check_link_status()
        debug_msg(
            "* Listening on port={}, ip={}".format(
                port, self.pretty_ip(self.ip_address)
            ),
            self._debug,
        )
        # Initialize a socket and set the mode
        self.src_port = port
        self.socket_open(socket_num, conn_mode=conn_mode)
        self.src_port = 0
        # Send listen command
        self._write_sncr(socket_num, _CMD_SOCK_LISTEN)
        # Wait until ready
        status = SNSR_SOCK_CLOSED
        while status not in (
            SNSR_SOCK_LISTEN,
            SNSR_SOCK_ESTABLISHED,
            _SNSR_SOCK_UDP,
        ):
            status = self._read_snsr(socket_num)
            if status == SNSR_SOCK_CLOSED:
                raise RuntimeError("Listening socket closed.")

    def socket_accept(self, socket_num: int) -> Tuple[int, Tuple[str, int]]:
        """
        Destination IPv4 address and port from an incoming connection.

        Return the next socket number so listening can continue, along with
        the IP address and port of the incoming connection.

        :param int socket_num: Socket number with connection to check.

        :return Tuple[int, Tuple[Union[str, bytearray], Union[int, bytearray]]]:
            If successful, the next (socket number, (destination IP address, destination port)).

        :raises ValueError: If the socket number is out of range.
        """
        self._sock_num_in_range(socket_num)
        dest_ip = self.remote_ip(socket_num)
        dest_port = self.remote_port(socket_num)
        next_socknum = self.get_socket()
        debug_msg(
            "Dest is ({}, {}), Next listen socknum is #{}".format(
                dest_ip, dest_port, next_socknum
            ),
            self._debug,
        )
        return next_socknum, (dest_ip, dest_port)

    def socket_open(self, socket_num: int, conn_mode: int = _SNMR_TCP) -> None:
        """
        Open an IP socket.

        The socket may connect via TCP or UDP protocols.

        :param int socket_num: The socket number to open.
        :param int conn_mode: The protocol to use. Use SNMR_TCP for TCP or SNMR_UDP for \
            UDP, defaults to SNMR_TCP.

        :raises ValueError: If the socket number is out of range.
        :raises ConnectionError: If the Ethernet link is down or no connection to socket.
        :raises RuntimeError: If unable to open a socket in UDP or TCP mode.
        """
        self._sock_num_in_range(socket_num)
        self._check_link_status()
        debug_msg("*** Opening socket {}".format(socket_num), self._debug)
        if self._read_snsr(socket_num) not in (
            SNSR_SOCK_CLOSED,
            SNSR_SOCK_TIME_WAIT,
            SNSR_SOCK_FIN_WAIT,
            SNSR_SOCK_CLOSE_WAIT,
            _SNSR_SOCK_CLOSING,
            _SNSR_SOCK_UDP,
        ):
            raise ConnectionError("Failed to initialize a connection with the socket.")
        debug_msg("* Opening W5k Socket, protocol={}".format(conn_mode), self._debug)
        time.sleep(0.00025)

        self._write_snmr(socket_num, conn_mode)
        self.write_snir(socket_num, 0xFF)

        if self.src_port > 0:
            # write to socket source port
            self._write_sock_port(socket_num, self.src_port)
        else:
            s_port = randint(49152, 65535)
            while s_port in self._src_ports_in_use:
                s_port = randint(49152, 65535)
            self._write_sock_port(socket_num, s_port)
            self._src_ports_in_use[socket_num] = s_port

        # open socket
        self._write_sncr(socket_num, _CMD_SOCK_OPEN)
        if self._read_snsr(socket_num) not in [_SNSR_SOCK_INIT, _SNSR_SOCK_UDP]:
            raise RuntimeError("Could not open socket in TCP or UDP mode.")

    def socket_close(self, socket_num: int) -> None:
        """
        Close a socket.

        :param int socket_num: The socket to close.

        :raises ValueError: If the socket number is out of range.
        """
        debug_msg("*** Closing socket {}".format(socket_num), self._debug)
        self._sock_num_in_range(socket_num)
        self._write_sncr(socket_num, _CMD_SOCK_CLOSE)
        debug_msg("  Waiting for socket to close…", self._debug)
        timeout = time.monotonic() + 5.0
        while self._read_snsr(socket_num) != SNSR_SOCK_CLOSED:
            if time.monotonic() > timeout:
                raise RuntimeError(
                    "Wiznet5k failed to close socket, status = {}.".format(
                        self._read_snsr(socket_num)
                    )
                )
            time.sleep(0.0001)
        debug_msg("  Socket has closed.", self._debug)

    def socket_disconnect(self, socket_num: int) -> None:
        """
        Disconnect a TCP or UDP connection.

        :param int socket_num: The socket to close.

        :raises ValueError: If the socket number is out of range.
        """
        debug_msg("*** Disconnecting socket {}".format(socket_num), self._debug)
        self._sock_num_in_range(socket_num)
        self._write_sncr(socket_num, _CMD_SOCK_DISCON)

    def socket_read(self, socket_num: int, length: int) -> Tuple[int, bytes]:
        """
        Read data from a hardware socket. Called directly by TCP socket objects and via
        read_udp() for UDP socket objects.

        :param int socket_num: The socket to read data from.
        :param int length: The number of bytes to read from the socket.

        :returns Tuple[int, bytes]: If the read was successful then the first
            item of the tuple is the length of the data and the second is the data.
            If the read was unsuccessful then 0, b"" is returned.

        :raises ValueError: If the socket number is out of range.
        :raises ConnectionError: If the Ethernet link is down.
        :raises RuntimeError: If the socket connection has been lost.
        """
        self._sock_num_in_range(socket_num)
        self._check_link_status()

        # Check if there is data available on the socket
        bytes_on_socket = self._get_rx_rcv_size(socket_num)
        debug_msg("Bytes avail. on sock: {}".format(bytes_on_socket), self._debug)
        if bytes_on_socket:
            bytes_on_socket = length if bytes_on_socket > length else bytes_on_socket
            debug_msg(
                "* Processing {} bytes of data".format(bytes_on_socket), self._debug
            )
            # Read the starting save address of the received data.
            pointer = self._read_snrx_rd(socket_num)
            # Read data from the hardware socket.
            bytes_read = self._chip_socket_read(socket_num, pointer, bytes_on_socket)
            # After reading the received data, update Sn_RX_RD register.
            pointer = (pointer + bytes_on_socket) & 0xFFFF
            self._write_snrx_rd(socket_num, pointer)
            self._write_sncr(socket_num, _CMD_SOCK_RECV)
        else:
            # no data on socket
            if self._read_snmr(socket_num) in (
                SNSR_SOCK_LISTEN,
                SNSR_SOCK_CLOSED,
                SNSR_SOCK_CLOSE_WAIT,
            ):
                raise RuntimeError("Lost connection to peer.")
            bytes_read = b""
        return bytes_on_socket, bytes_read

    def read_udp(self, socket_num: int, length: int) -> Tuple[int, bytes]:
        """
        Read UDP socket's current message bytes.

        :param int socket_num: The socket to read data from.
        :param int length: The number of bytes to read from the socket.

        :return Tuple[int, bytes]: If the read was successful then the first
            item of the tuple is the length of the data and the second is the data.
            If the read was unsuccessful then (0, b"") is returned.

        :raises ValueError: If the socket number is out of range.
        """
        self._sock_num_in_range(socket_num)
        bytes_on_socket, bytes_read = 0, b""
        # Parse the UDP packet header.
        header_length, self._pbuff[:8] = self.socket_read(socket_num, 8)
        if header_length:
            if header_length != 8:
                raise ValueError("Invalid UDP header.")
            data_length = self._chip_parse_udp_header(socket_num)
            # Read the UDP packet data.
            if data_length:
                if data_length <= length:
                    bytes_on_socket, bytes_read = self.socket_read(
                        socket_num, data_length
                    )
                else:
                    bytes_on_socket, bytes_read = self.socket_read(socket_num, length)
                    # just consume the rest, it is lost to the higher layers
                    self.socket_read(socket_num, data_length - length)
        return bytes_on_socket, bytes_read

    def socket_write(
        self, socket_num: int, buffer: bytearray, timeout: float = 0.0
    ) -> int:
        """
        Write data to a socket.

        :param int socket_num: The socket to write to.
        :param bytearray buffer: The data to write to the socket.
        :param float timeout: Write data timeout in seconds, defaults to 0.0 which waits
            indefinitely.

        :return int: The number of bytes written to the socket.

        :raises ConnectionError: If the Ethernet link is down.
        :raises ValueError: If the socket number is out of range.
        :raises RuntimeError: If the data cannot be sent.
        """
        self._sock_num_in_range(socket_num)
        self._check_link_status()
        if len(buffer) > _SOCK_SIZE:
            bytes_to_write = _SOCK_SIZE
        else:
            bytes_to_write = len(buffer)
        stop_time = time.monotonic() + timeout

        # If buffer is available, start the transfer
        free_size = self._get_tx_free_size(socket_num)
        while free_size < bytes_to_write:
            free_size = self._get_tx_free_size(socket_num)
            status = self.socket_status(socket_num)
            if status not in (SNSR_SOCK_ESTABLISHED, SNSR_SOCK_CLOSE_WAIT) or (
                timeout and time.monotonic() > stop_time
            ):
                raise RuntimeError("Unable to write data to the socket.")

        # Read the starting address for saving the transmitting data.
        pointer = self._read_sntx_wr(socket_num)
        offset = pointer & _SOCK_MASK
        self._chip_socket_write(socket_num, offset, bytes_to_write, buffer)
        # update sn_tx_wr to the value + data size
        pointer = (pointer + bytes_to_write) & 0xFFFF
        self._write_sntx_wr(socket_num, pointer)
        self._write_sncr(socket_num, _CMD_SOCK_SEND)

        # check data was  transferred correctly
        while not self.read_snir(socket_num) & _SNIR_SEND_OK:
            if self.socket_status(socket_num) in (
                SNSR_SOCK_CLOSED,
                SNSR_SOCK_TIME_WAIT,
                SNSR_SOCK_FIN_WAIT,
                SNSR_SOCK_CLOSE_WAIT,
                _SNSR_SOCK_CLOSING,
            ):
                raise RuntimeError("No data was sent, socket was closed.")
            if timeout and time.monotonic() > stop_time:
                raise RuntimeError("Operation timed out. No data sent.")
            if self.read_snir(socket_num) & SNIR_TIMEOUT:
                self.write_snir(socket_num, SNIR_TIMEOUT)
                # TCP sockets are closed by the hardware timeout
                # so that will be caught at the while statement.
                # UDP sockets are 1:many so not closed thus return 0.
                if self._read_snmr(socket_num) == SNMR_UDP:
                    return 0
            time.sleep(0.001)
        self.write_snir(socket_num, _SNIR_SEND_OK)
        return bytes_to_write

    def sw_reset(self) -> None:
        """
        Soft reset and reinitialize the WIZnet chip.

        :raises RuntimeError: If reset fails.
        """
        self._wiznet_chip_init()

    def _sw_reset_5x00(self) -> bool:
        """
        Perform a soft reset on the WIZnet 5100s and 5500 chips.

        :returns bool: True if reset was success
        """
        self._write_mr(_MR_RST)
        time.sleep(0.05)
        return self._read_mr() == {"w5500": 0x00, "w5100s": 0x03}[self._chip_type]

    def _wiznet_chip_init(self) -> None:
        """
        Detect and initialize a WIZnet 5k Ethernet module.

        :raises RuntimeError: If no WIZnet chip is detected.
        """

        def _setup_sockets() -> None:
            """Initialise sockets for w5500 and w6100 chips."""
            for sock_num in range(_MAX_SOCK_NUM[self._chip_type]):
                ctrl_byte = 0x0C + (sock_num << 5)
                self._write(0x1E, ctrl_byte, 2)
                self._write(0x1F, ctrl_byte, 2)
            self._ch_base_msb = 0x00
            WIZNET5K._sockets_reserved = [False] * (_MAX_SOCK_NUM[self._chip_type] - 1)
            self._src_ports_in_use = [0] * _MAX_SOCK_NUM[self._chip_type]

        def _detect_and_reset_w6100() -> bool:
            """
            Detect and reset a W6100 chip. Called at startup to initialize the
            interface hardware.

            :return bool: True if a W6100 chip is detected, False if not.
            """
            self._chip_type = "w6100"

            # Reset w6100
            self._write(0x41F4, 0x04, 0xCE)  # Unlock chip settings.
            time.sleep(0.05)  # Wait for unlock.
            self._write(0x2004, 0x04, 0x00)  # Reset chip.
            time.sleep(0.05)  # Wait for reset.

            if self._read(_REG_VERSIONR[self._chip_type], 0x00)[0] != 0x61:
                return False
            # Initialize w6100.
            self._write(0x41F5, 0x04, 0x3A)  # Unlock network settings.
            _setup_sockets()
            return True

        def _detect_and_reset_w5500() -> bool:
            """
            Detect and reset a W5500 chip. Called at startup to initialize the
            interface hardware.

            :return bool: True if a W5500 chip is detected, False if not.
            """
            self._chip_type = "w5500"
            if not self._sw_reset_5x00():
                return False

            self._write_mr(0x08)
            if self._read_mr() != 0x08:
                return False

            self._write_mr(0x10)
            if self._read_mr() != 0x10:
                return False

            self._write_mr(0x00)
            if self._read_mr() != 0x00:
                return False

            if self._read(_REG_VERSIONR[self._chip_type], 0x00)[0] != 0x04:
                return False
            # Initialize w5500
            _setup_sockets()
            return True

        def _detect_and_reset_w5100s() -> bool:
            """
            Detect and reset a W5100S chip. Called at startup to initialize the
            interface hardware.

            :return bool: True if a W5100 chip is detected, False if not.
            """
            self._chip_type = "w5100s"
            if not self._sw_reset_5x00():
                return False

            if self._read(_REG_VERSIONR[self._chip_type], 0x00)[0] != 0x51:
                return False

            # Initialise w5100s
            self._ch_base_msb = 0x0400
            WIZNET5K._sockets_reserved = [False] * (_MAX_SOCK_NUM[self._chip_type] - 1)
            self._src_ports_in_use = [0] * _MAX_SOCK_NUM[self._chip_type]
            return True

        for func in [
            _detect_and_reset_w5100s,
            _detect_and_reset_w5500,
            _detect_and_reset_w6100,
        ]:
            if func():
                return
        self._chip_type = None
        raise RuntimeError("Failed to initialize WIZnet module.")

    def _sock_num_in_range(self, sock: int) -> None:
        """Check that the socket number is in the range 0 - maximum sockets."""
        if not 0 <= sock < self.max_sockets:
            raise ValueError("Socket number out of range.")

    def _check_link_status(self):
        """Raise an exception if the link is down."""
        if not self.link_status:
            raise ConnectionError("The Ethernet connection is down.")

    @staticmethod
    def _read_socket_reservations() -> list[int]:
        """Return the list of reserved sockets."""
        return WIZNET5K._sockets_reserved

    def _read_mr(self) -> int:
        """Read from the Mode Register (MR)."""
        return int.from_bytes(self._read(_REG_MR[self._chip_type], 0x00), "big")

    def _write_mr(self, data: int) -> None:
        """Write to the mode register (MR)."""
        self._write(_REG_MR[self._chip_type], 0x04, data)

    # *** Low Level Methods ***

    def _read(
        self,
        addr: int,
        callback: int,
        length: int = 1,
    ) -> bytes:
        """
        Read data from a register address.

        :param int addr: Register address to read.
        :param int callback: Callback reference.
        :param int length: Number of bytes to read from the register, defaults to 1.

        :return bytes: Data read from the chip.
        """
        with self._device as bus_device:
            self._chip_read(bus_device, addr, callback)
            self._rxbuf = bytearray(length)
            bus_device.readinto(self._rxbuf)
            return bytes(self._rxbuf)

    def _write(self, addr: int, callback: int, data: Union[int, bytes]) -> None:
        """
        Write data to a register address.

        :param int addr: Destination address.
        :param int callback: Callback reference.
        :param Union[int, bytes] data: Data to write to the register address, if data
            is an integer, it must be 1 or 2 bytes.

        :raises OverflowError: if integer data is more than 2 bytes.
        """
        with self._device as bus_device:
            self._chip_write(bus_device, addr, callback)
            try:
                data = data.to_bytes(1, "big")
            except OverflowError:
                data = data.to_bytes(2, "big")
            except AttributeError:
                pass
            bus_device.write(data)

    def _read_two_byte_sock_reg(self, sock: int, reg_address: int) -> int:
        """Read a two byte socket register."""
        register = self._read_socket_register(sock, reg_address) << 8
        register += self._read_socket_register(sock, reg_address + 1)
        return register

    def _write_two_byte_sock_reg(self, sock: int, reg_address: int, data: int) -> None:
        """Write to a two byte socket register."""
        self._write_socket_register(sock, reg_address, data >> 8 & 0xFF)
        self._write_socket_register(sock, reg_address + 1, data & 0xFF)

    # *** Socket Register Methods ***

    def _get_rx_rcv_size(self, sock: int) -> int:
        """Size of received and saved in socket buffer."""
        val = 0
        val_1 = self._read_snrx_rsr(sock)
        while val != val_1:
            val_1 = self._read_snrx_rsr(sock)
            if val_1 != 0:
                val = self._read_snrx_rsr(sock)
        return val

    def _get_tx_free_size(self, sock: int) -> int:
        """Free size of socket's tx buffer block."""
        val = 0
        val_1 = self._read_sntx_fsr(sock)
        while val != val_1:
            val_1 = self._read_sntx_fsr(sock)
            if val_1 != 0:
                val = self._read_sntx_fsr(sock)
        return val

    def _read_snrx_rd(self, sock: int) -> int:
        """Read socket n RX Read Data Pointer Register."""
        return self._read_two_byte_sock_reg(sock, _REG_SNRX_RD[self._chip_type])

    def _write_snrx_rd(self, sock: int, data: int) -> None:
        """Write socket n RX Read Data Pointer Register."""
        self._write_two_byte_sock_reg(sock, _REG_SNRX_RD[self._chip_type], data)

    def _read_sntx_wr(self, sock: int) -> int:
        """Read the socket write buffer pointer for socket `sock`."""
        return self._read_two_byte_sock_reg(sock, _REG_SNTX_WR[self._chip_type])

    def _write_sntx_wr(self, sock: int, data: int) -> None:
        """Write the socket write buffer pointer for socket `sock`."""
        self._write_two_byte_sock_reg(sock, _REG_SNTX_WR[self._chip_type], data)

    def _read_sntx_fsr(self, sock: int) -> int:
        """Read socket n TX Free Size Register"""
        return self._read_two_byte_sock_reg(sock, _REG_SNTX_FSR[self._chip_type])

    def _read_snrx_rsr(self, sock: int) -> int:
        """Read socket n Received Size Register"""
        return self._read_two_byte_sock_reg(sock, _REG_SNRX_RSR[self._chip_type])

    def _read_sndipr(self, sock) -> bytes:
        """Read socket destination IP address."""
        data = []
        for offset in range(4):
            data.append(
                self._read_socket_register(sock, _REG_SNDIPR[self._chip_type] + offset)
            )
        return bytes(data)

    def _write_sndipr(self, sock: int, ip_addr: bytes) -> None:
        """Write to socket destination IP Address."""
        for offset, value in enumerate(ip_addr):
            self._write_socket_register(
                sock, _REG_SNDIPR[self._chip_type] + offset, value
            )

    def _read_sndport(self, sock: int) -> int:
        """Read socket destination port."""
        return self._read_two_byte_sock_reg(sock, _REG_SNDPORT[self._chip_type])

    def _write_sndport(self, sock: int, port: int) -> None:
        """Write to socket destination port."""
        self._write_two_byte_sock_reg(sock, _REG_SNDPORT[self._chip_type], port)

    def _read_snsr(self, sock: int) -> int:
        """Read Socket n Status Register."""
        return self._read_socket_register(sock, _REG_SNSR[self._chip_type])

    def read_snir(self, sock: int) -> int:
        """Read Socket n Interrupt Register."""
        return self._read_socket_register(sock, _REG_SNIR[self._chip_type])

    def write_snir(self, sock: int, data: int) -> None:
        """Write to Socket n Interrupt Register."""
        self._write_socket_register(sock, _REG_SNIR[self._chip_type], data)

    def _read_snmr(self, sock: int) -> int:
        """Read the socket MR register."""
        return self._read_socket_register(sock, _REG_SNMR)

    def _write_snmr(self, sock: int, protocol: int) -> None:
        """Write to Socket n Mode Register."""
        self._write_socket_register(sock, _REG_SNMR, protocol)

    def _write_sock_port(self, sock: int, port: int) -> None:
        """Write to the socket port number."""
        self._write_two_byte_sock_reg(sock, _REG_SNPORT[self._chip_type], port)

    def _write_sncr(self, sock: int, data: int) -> None:
        """Write to socket command register."""
        self._write_socket_register(sock, _REG_SNCR[self._chip_type], data)
        # Wait for command to complete before continuing.
        while self._read_socket_register(sock, _REG_SNCR[self._chip_type]):
            pass

    @property
    def rcr(self) -> int:
        """Retry count register."""
        return int.from_bytes(self._read(_REG_RCR[self._chip_type], 0x00), "big")

    @rcr.setter
    def rcr(self, retry_count: int) -> None:
        """Retry count register."""
        if 0 > retry_count > 255:
            raise ValueError("Retries must be from 0 to 255.")
        self._write(_REG_RCR[self._chip_type], 0x04, retry_count)

    @property
    def rtr(self) -> int:
        """Retry time register."""
        return int.from_bytes(self._read(_REG_RTR[self._chip_type], 0x00, 2), "big")

    @rtr.setter
    def rtr(self, retry_time: int) -> None:
        """Retry time register."""
        if 0 > retry_time >= 2**16:
            raise ValueError("Retry time must be from 0 to 65535")
        self._write(_REG_RTR[self._chip_type], 0x04, retry_time)

    # *** Chip Specific Methods ***

    def _chip_read(self, device: "busio.SPI", address: int, call_back: int) -> None:
        """Chip specific calls for _read method."""
        if self._chip_type in ("w5500", "w6100"):
            device.write((address >> 8).to_bytes(1, "big"))
            device.write((address & 0xFF).to_bytes(1, "big"))
            device.write(call_back.to_bytes(1, "big"))
        elif self._chip_type == "w5100s":
            device.write((0x0F).to_bytes(1, "big"))
            device.write((address >> 8).to_bytes(1, "big"))
            device.write((address & 0xFF).to_bytes(1, "big"))

    def _chip_write(self, device: "busio.SPI", address: int, call_back: int) -> None:
        """Chip specific calls for _write."""
        if self._chip_type in ("w5500", "w6100"):
            device.write((address >> 8).to_bytes(1, "big"))
            device.write((address & 0xFF).to_bytes(1, "big"))
            device.write(call_back.to_bytes(1, "big"))
        elif self._chip_type == "w5100s":
            device.write((0xF0).to_bytes(1, "big"))
            device.write((address >> 8).to_bytes(1, "big"))
            device.write((address & 0xFF).to_bytes(1, "big"))

    def _chip_socket_read(self, socket_number, pointer, bytes_to_read):
        """Chip specific calls for socket_read."""
        if self._chip_type in ("w5500", "w6100"):
            # Read data from the starting address of snrx_rd
            ctrl_byte = 0x18 + (socket_number << 5)
            bytes_read = self._read(pointer, ctrl_byte, bytes_to_read)
        elif self._chip_type == "w5100s":
            offset = pointer & _SOCK_MASK
            src_addr = offset + (socket_number * _SOCK_SIZE + 0x6000)
            if offset + bytes_to_read > _SOCK_SIZE:
                split_point = _SOCK_SIZE - offset
                bytes_read = self._read(src_addr, 0x00, split_point)
                split_point = bytes_to_read - split_point
                src_addr = socket_number * _SOCK_SIZE + 0x6000
                bytes_read += self._read(src_addr, 0x00, split_point)
            else:
                bytes_read = self._read(src_addr, 0x00, bytes_to_read)
        return bytes_read

    def _chip_socket_write(
        self, socket_number: int, offset: int, bytes_to_write: int, buffer: bytes
    ):
        """Chip specific calls for socket_write."""
        if self._chip_type in ("w5500", "w6100"):
            dst_addr = offset + (socket_number * _SOCK_SIZE + 0x8000)
            cntl_byte = 0x14 + (socket_number << 5)
            self._write(dst_addr, cntl_byte, buffer[:bytes_to_write])

        elif self._chip_type == "w5100s":
            dst_addr = offset + (socket_number * _SOCK_SIZE + 0x4000)

            if offset + bytes_to_write > _SOCK_SIZE:
                split_point = _SOCK_SIZE - offset
                self._write(dst_addr, 0x00, buffer[:split_point])
                dst_addr = socket_number * _SOCK_SIZE + 0x4000
                self._write(dst_addr, 0x00, buffer[split_point:bytes_to_write])
            else:
                self._write(dst_addr, 0x00, buffer[:bytes_to_write])

    def _chip_parse_udp_header(self, socket_num) -> int:
        """
        Parse chip specific UDP header data for IPv4 packets.

        Sets the source IPv4 address and port number and returns the UDP data length.

        :return int: The UDP data length.
        """
        if self._chip_type in ("w5100s", "w5500"):
            self.udp_from_ip[socket_num] = self._pbuff[:4]
            self.udp_from_port[socket_num] = int.from_bytes(self._pbuff[4:6], "big")
            return int.from_bytes(self._pbuff[6:], "big")
        if self._chip_type == "w6100":
            self.udp_from_ip[socket_num] = self._pbuff[3:7]
            self.udp_from_port[socket_num] = int.from_bytes(self._pbuff[6:], "big")
            return int.from_bytes(self._pbuff[:2], "big") & 0x07FF
        raise ValueError("Unsupported chip type.")

    def _write_socket_register(self, sock: int, address: int, data: int) -> None:
        """Write to a WIZnet 5k socket register."""
        if self._chip_type in ("w5500", "w6100"):
            cntl_byte = (sock << 5) + 0x0C
            self._write(address, cntl_byte, data)
        elif self._chip_type == "w5100s":
            cntl_byte = 0
            self._write(self._ch_base_msb + sock * _CH_SIZE + address, cntl_byte, data)

    def _read_socket_register(self, sock: int, address: int) -> int:
        """Read a WIZnet 5k socket register."""
        if self._chip_type in ("w5500", "w6100"):
            cntl_byte = (sock << 5) + 0x08
            register = self._read(address, cntl_byte)
        elif self._chip_type == "w5100s":
            cntl_byte = 0
            register = self._read(
                self._ch_base_msb + sock * _CH_SIZE + address, cntl_byte
            )
        return int.from_bytes(register, "big")

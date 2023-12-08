# SPDX-FileCopyrightText: 2023 Martin Stephens
#
# SPDX-License-Identifier: MIT

"""Makes a debug message function available to all modules."""
try:
    from typing import TYPE_CHECKING, Union

    if TYPE_CHECKING:
        from adafruit_wiznet5k.adafruit_wiznet5k import WIZNET5K
except ImportError:
    pass

import gc


def debug_msg(
    message: Union[Exception, str, bytes, bytearray], debugging: bool
) -> None:
    """
    Helper function to print debugging messages. If the message is a bytes type
    object, create a hexdump.

    :param Union[Exception, str, bytes, bytearray] message: The message to print.
    :param bool debugging: Only print if debugging is True.
    """
    if debugging:
        if isinstance(message, (bytes, bytearray)):
            message = _hexdump(message)
        print(message)
        del message
        gc.collect()


def _hexdump(src: bytes):
    """
    Create a 16 column hexdump of a bytes object.

    :param bytes src: The bytes object to hexdump.

    :returns str: The hexdump.
    """
    result = []
    for i in range(0, len(src), 16):
        chunk = src[i : i + 16]
        hexa = " ".join(("{:02x}".format(x) for x in chunk))
        text = "".join((chr(x) if 0x20 <= x < 0x7F else "." for x in chunk))
        result.append("{:04x}   {:<48}   {}".format(i, hexa, text))
    return "\n".join(result)

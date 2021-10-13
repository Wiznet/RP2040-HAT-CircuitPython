> ## TCP(Transmission Control Protocol)

[W5x00_Echo_Demo_TCP.py](https://github.com/Wiznet/RP2040-HAT-CircuitPython/blob/master/examples/Network/W5x00_Echo_Demo_TCP.py)

- Establish a session to ensure accurate transmission by ensuring the destination and destination.

- Establish a connection through a 3-way handshake process and release it through 4-way handshake.
- It guarantees high reliability.
- The server and the client are connected one-on-one.
- The speed is slow.

![][link-tcpflow]

> ## UDP(User Datagram Protocol)

[W5x00_Echo_Demo_UDP.py](https://github.com/Wiznet/RP2040-HAT-CircuitPython/blob/master/examples/Network/W5x00_Echo_Demo_UDP.py)

- Since UDP is a non-connected service, there is no process of establishing and disconnecting the connection.
- It is often used for services where continuity is more important than reliability, such as real-time streaming.

- It's not reliable.
- The server and the client may be connected to each other by 1 to 1, 1 to N, and N to M.

- The speed is fast.

![][link-udpflow]

> ## PING(Packet Internet Grouper)

[W5x00_Ping_Test.py](https://github.com/Wiznet/RP2040-HAT-CircuitPython/blob/master/examples/Network/W5x00_Ping_Test.py)

- Check if the network is connected normally and if the data is sent to each other.

> This is the code to set the IP of 192.168.1.100

> I hope that the PC also has an environment that communicates with 192.168.1.xxx.

Copy the content to code.py on your RPi Pico and save.

![][link-ping_1]

Let's run the PING test on the laptop, and the results will show as below.

![][link-ping_2]



> ## Reset

[W5x00_Reset_Test.py](https://github.com/Wiznet/RP2040-HAT-CircuitPython/blob/master/examples/Network/W5x00_Reset_Test.py)

- Set Hardware before Reset.
- Set HOST Interface Mode with MOD [3:0] pin.
- Supply the Reset signal longer than 500ns on RSTn pin for Hardware Reset.

![][link-reset]



> ## Sendfile_UDP

- It is a file transfer program using UDP-based Socket.
- Implement UDP File Transfer that delivers files.

1. Enter the file name to be transferred.

![][link-sendfile_udp_1]

2. Successfully transferred the file.

![][link-sendfile_udp_2]



## Attach

Attach a flow that operates through [WIRESHARK](https://www.wireshark.org/#download)

- [TCP.pcapng](https://github.com/Wiznet/RP2040-HAT-CircuitPython/blob/master/examples/Network/TCP.pcapng)
- [UDP.pcapng](https://github.com/Wiznet/RP2040-HAT-CircuitPython/blob/master/examples/Network/UDP.pcapng)
- [PING.pcapng](https://github.com/Wiznet/RP2040-HAT-CircuitPython/blob/master/examples/Network/PING.pcapng)

<!--

Link

-->

[link-tcpflow]: https://github.com/Wiznet/RP2040-HAT-CircuitPython/blob/master/images/NETWORK/TCP%20flow.jpg
[link-udpflow]: https://github.com/Wiznet/RP2040-HAT-CircuitPython/blob/master/images/NETWORK/UDP%20flow.jpg
[link-ping_1]: https://github.com/Wiznet/RP2040-HAT-CircuitPython/blob/master/images/NETWORK/Pico_PING_1.jpg
[link-ping_2]: https://github.com/Wiznet/RP2040-HAT-CircuitPython/blob/master/images/NETWORK/Pico_PING_2.jpg
[link-reset]: https://github.com/Wiznet/RP2040-HAT-CircuitPython/blob/master/images/NETWORK/reset.jpg
[link-sendfile_udp_1]:https://github.com/Wiznet/RP2040-HAT-CircuitPython/blob/master/images/NETWORK/sendfile_udp_1.jpg
[link-sendfile_udp_2]:https://github.com/Wiznet/RP2040-HAT-CircuitPython/blob/master/images/NETWORK/sendfile_udp_2.jpg


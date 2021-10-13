# How to Test DNS Example

![][link-DNS]



## Step 1: Prepare Software

> The following serial terminal program is required for **DNS** test, download and install from below links.

### &#10004;[**Tera Term**][link-tera_term]  or  &#10004; [**Hercules**][link-hercules]




## Step 2: Prepare hardware

1. Combine WIZnet Ethernet HAT with Raspberry Pi Pico.
2. Connect ethernet cable to Ethernet HAT ethernet port.
3. Connect Raspberry Pi Pico to desktop or laptop using 5 pin micro USB cable.



If you use W5100S-EVB-Pico, you can skip '1. Combine...'



## Step 3: Setup DNS Example

> To test the **DNS example**, minor settings shall be done in code.



1. Setup SPI and Reset pin.

```python
##SPI0
SPI0_SCK = board.GP18
SPI0_TX = board.GP19
SPI0_RX = board.GP16
SPI0_CSn = board.GP17

##reset
W5x00_RSTn = board.GP20
```

2. Initialize DHCP

```python
# Setup your network configuration below
# random MAC, later should change this value on your vendor ID
MY_MAC = (0x00, 0x01, 0x02, 0x03, 0x04, 0x05)
```

```python
# Initialize ethernet interface with DHCP
eth = WIZNET5K(spi_bus, cs, is_dhcp=True, mac=MY_MAC, debug=False)
```

3. Convert the **URL** of the server to the **IP address**.

```python
print("DNS Translate : DNS Server        -->> %s" % eth.pretty_ip(eth.get_host_by_name("kns.kornet.net")))  #DNS Domain
```

4. Copy **DNS code** to **code.py** on your RPi Pico and save. Make sure that PC is configured in same subnet 192.168.1.xxx.



## Step 4: Upload and Run

1. Check COMport in [Device Manager] and then open Serial Terminal.

![][link-port]![link-terminal]

2. Access the domain URL of the server and convert it to an IP address.

![][link-DNS_2]



## Attach

Attach a flow that operates through [WIRESHARK](https://www.wireshark.org/#download).

- [DNS.pcapng](https://github.com/Wiznet/RP2040-HAT-CircuitPython/blob/master/examples/DNS/DNS.pcapng)



 [**◀ Go to Ethernet example structure**](#ethernet_example_structure)





<!--
Link
-->

[link-tera_term]: https://osdn.net/projects/ttssh2/releases/
[link-hercules]: https://www.hw-group.com/software/hercules-setup-utility
[link-DNS]:  https://github.com/Wiznet/RP2040-HAT-CircuitPython/blob/master/images/DNS/DNS.png



[link-port]: https://github.com/Wiznet/RP2040-HAT-CircuitPython/blob/master/images/DNS/PORT.jpg
[link-Terminal]:https://github.com/Wiznet/RP2040-HAT-CircuitPython/blob/master/images/DNS/Terminal.jpg

[link-DNS_1]: https://github.com/Wiznet/RP2040-HAT-CircuitPython/blob/master/images/DNS/PICO_DNS_0.png
[link-DNS_2]: https://github.com/Wiznet/RP2040-HAT-CircuitPython/blob/master/images/DNS/PICO_DNS.PNG

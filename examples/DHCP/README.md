# How to Test DHCP Example

![][link-DHCP]

## Step 1: Prepare Software

> The following serial terminal program is required for **DHCP** test, download and install from below links.

### &#10004; [**Tera Term**][link-tera_term] or &#10004; [**Hercules**][link-hercules]



## Step 2: Prepare hardware

1. Combine WIZnet Ethernet HAT with Raspberry Pi Pico.
2. Connect ethernet cable to Ethernet HAT ethernet port.
3. Connect Raspberry Pi Pico to desktop or laptop using 5 pin micro USB cable.



If you use W5100S-EVB-Pico, you can skip '1. Combine...'



## Step 3: Setup DHCP Example

To test the **DHCP example**, minor settings shall be done in code.

1. Setup SPI0 and Reset pin.

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

   2-1. Set **IP address** and disable DHCP.

   ```python
   # Setup your network configuration below
   # random MAC, later should change this value on your vendor ID
   MY_MAC = (0x00, 0x01, 0x02, 0x03, 0x04, 0x05)
   IP_ADDRESS = (192, 168, 1, 100)
   SUBNET_MASK = (255, 255, 255, 0)
   GATEWAY_ADDRESS = (192, 168, 1, 1)
   DNS_SERVER = (8, 8, 8, 8)
   ```

   ```python
   # Initialize ethernet interface without DHCP
   eth = WIZNET5K(spi_bus, cs, is_dhcp=False, mac=MY_MAC, debug=False
   # Set network configuration
   eth.ifconfig = (IP_ADDRESS, SUBNET_MASK, GATEWAY_ADDRESS, DNS_SERVER)
   ```

   

   2-2. enable DHCP

   ```python
   # Setup your network configuration below
   # random MAC, later should change this value on your vendor ID
   MY_MAC = (0x00, 0x01, 0x02, 0x03, 0x04, 0x05)
   ```

   ```python
   # Initialize ethernet interface with DHCP
   eth = WIZNET5K(spi_bus, cs, is_dhcp=True, mac=MY_MAC, debug=False)
   ```

   

3. Copy **DHCP code** to **code.py** on your RPi Pico and save. This DHCP enable code sets IP to 192.168.1.100. Make sure that PC is configured in same subnet 192.168.1.xxx.



## Step 4: Upload and Run

1. Check COMport in [Device Manager] and then open Serial Terminal.

![][link-port]![link-terminal]

2. Allocates IP address to Statistically **without DHCP**. Open the command on your PC and conduct the **PING test**.

![][link-DHCP_1]![][link-DHCP_2]

3. Automatic IP address assigned **using DHCP**. Open the command on your PC and conduct the **PING test**.

![][link-DHCP_3]![][link-DHCP_4]



## Attach

Attach a flow that operates through [WIRESHARK](https://www.wireshark.org/#download).

- [DHCP.pcapng](https://github.com/Wiznet/RP2040-HAT-CircuitPython/blob/master/examples/DHCP/DHCP.pcapng)




 [**◀ Go to Ethernet example structure**](#ethernet_example_structure)

<!--
Link
-->

[link-tera_term]: https://osdn.net/projects/ttssh2/releases/
[link-hercules]: https://www.hw-group.com/software/hercules-setup-utility
[link-DHCP]:  https://github.com/Wiznet/RP2040-HAT-CircuitPython/blob/master/images/DHCP/DHCP.png



[link-port]: https://github.com/Wiznet/RP2040-HAT-CircuitPython/blob/master/images/DHCP/PORT.jpg
[link-Terminal]:https://github.com/Wiznet/RP2040-HAT-CircuitPython/blob/master/images/DHCP/Terminal.jpg
[link-DHCP_0]:https://github.com/Wiznet/RP2040-HAT-CircuitPython/blob/master/images/DHCP/PICO_DHCP_0.png
[link-DHCP_1]:https://github.com/Wiznet/RP2040-HAT-CircuitPython/blob/master/images/DHCP/PICO_DHCP_1.PNG
[link-DHCP_2]:https://github.com/Wiznet/RP2040-HAT-CircuitPython/blob/master/images/DHCP/PICO_DHCP_2.PNG
[link-DHCP_3]:https://github.com/Wiznet/RP2040-HAT-CircuitPython/blob/master/images/DHCP/PICO_DHCP_3.PNG
[link-DHCP_4]:https://github.com/Wiznet/RP2040-HAT-CircuitPython/blob/master/images/DHCP/PICO_DHCP_4.PNG

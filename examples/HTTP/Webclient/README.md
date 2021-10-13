# How to WebClient Example

![][link-http]


## Step 1: Prepare Software

> The following serial terminal program is required for **Webclient** test, download and install from below links.

### &#10004;[**Tera Term**][link-tera_term]  or  &#10004; [**Hercules**][link-hercules]




## Step 2: Prepare hardware

1. Combine WIZnet Ethernet HAT with Raspberry Pi Pico.
2. Connect ethernet cable to Ethernet HAT ethernet port.
3. Connect Raspberry Pi Pico to desktop or laptop using 5 pin micro USB cable.



If you use W5100S-EVB-Pico, you can skip '1. Combine...'



## Step 3: Setup WebClinet Example

> To test the **Webclient example**, minor settings shall be done in code.



1. Setup SPI port and Reset pin.

```python
##SPI0
SPI0_SCK = board.GP18
SPI0_TX = board.GP19
SPI0_RX = board.GP16
SPI0_CSn = board.GP17

##reset
W5x00_RSTn = board.GP20
```

2. Initialize ethernet interface with DHCP

```python
eth = WIZNET5K(spi_bus, cs, is_dhcp=True, mac=MY_MAC, debug=False)
```

3. HTML request, Access **HTML URL** and **Json URL**

```python
TEXT_URL = "http://wifitest.adafruit.com/testwifi/index.html"
JSON_URL = "http://api.coindesk.com/v1/bpi/currentprice/USD.json"
```

4. Run Pico to open the web client.

```python
##run Webclient
while True:
    # Maintain DHCP lease
    eth.maintain_dhcp_lease()

    led.value = not led.value
    time.sleep(1)
```

5. Copy **Webclient code** to **code.py** on your RPi Pico and save. Make sure that PC is configured in same subnet 192.168.1.xxx.



## Step 4: Upload and Run

1. Check COMport in [Device Manager] and then open Serial Terminal.

![][link-port]![][link-terminal]

2. Use DNS to access the address of the server. After that, it accesses the server in each URL and prints the contents. The text of each URL is as follows.

![][link-webclient_1]

3. Text content in **HTML**.

![][link-webclient_2]

4. Text content in **Json**.

![][link-webclient_3]



## Attach

Attach a flow that operates through [WIRESHARK](https://www.wireshark.org/#download).

- [HTTP_Client.pcapng](https://github.com/Wiznet/RP2040-HAT-CircuitPython/blob/master/examples/HTTP/Webclient/HTTP_Client.pcapng)



 [**◀ Go to Ethernet example structure**](#ethernet_example_structure)






<!--
Link
-->

[link-tera_term]: https://osdn.net/projects/ttssh2/releases/
[link-hercules]: https://www.hw-group.com/software/hercules-setup-utility
[link-http]: https://github.com/Wiznet/RP2040-HAT-CircuitPython/blob/master/images/HTTP/HTTP_0.jpg
[link-http_0]: https://github.com/Wiznet-OpenHardware/RP2040-HAT-CircuitPython/blob/main/img/HTTP/HTTP.png



[link-port]:https://github.com/Wiznet/RP2040-HAT-CircuitPython/blob/master/images/HTTP/PORT.jpg
[link-terminal]: https://github.com/Wiznet/RP2040-HAT-CircuitPython/blob/master/images/HTTP/Terminal.jpg

[link-webclient_1]: https://github.com/Wiznet/RP2040-HAT-CircuitPython/blob/master/images/HTTP/Webclient_1.PNG
[link-webclient_2]: https://github.com/Wiznet/RP2040-HAT-CircuitPython/blob/master/images/HTTP/Webclient_2.PNG
[link-webclient_3]: https://github.com/Wiznet/RP2040-HAT-CircuitPython/blob/master/images/HTTP/Webclient_3.PNG

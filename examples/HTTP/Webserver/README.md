# How to WebServer Example

![][link-http]


## Step 1: Prepare Software

> The following serial terminal program is required for **Webserver** test, download and install from below links.

### &#10004;[**Tera Term**][link-tera_term]  or  &#10004; [**Hercules**][link-hercules]




## Step 2: Prepare hardware

1. Combine WIZnet Ethernet HAT with Raspberry Pi Pico.
2. Connect ethernet cable to Ethernet HAT ethernet port.
3. Connect Raspberry Pi Pico to desktop or laptop using 5 pin micro USB cable.



If you use W5100S-EVB-Pico, you can skip '1. Combine...'



## Step 3: Setup Webserver Example

> To test the **Webserver example**, minor settings shall be done in code.



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

2. Initialize ethernet interface with DHCP

```python
eth = WIZNET5K(spi_bus, cs, is_dhcp=True, mac=MY_MAC, debug=False)
```

3. HTML request

```python
html_string = '''
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta http-equiv="X-UA-Compatible" content="IE=edge">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>RaspberryPi Pico Web server - WIZnet W5100S/W5500</title>
</head>
<body>
<div align="center">
<H1>RaspberryPi Pico Web server & WIZnet Ethernet HAT</H1>
<h2>Network Information</h2>
<p>
Chip Version is $CHIPNAME<br>
My IP address is $IPADDRESS<br>
</p>
<h2>Control LED</h2>
<p>
<label for="led_on"></label><a href="/led_on" id="led_on"> [ON] </a><br>
</p>
<p>
<label for="led_off"></label><a href="/led_off" id="led_off"> [OFF] </a><br>
</p>
</div>
</body>
</html>
'''
```

4. Run Pico to open the web server.

```python
# Start the server
wsgiServer.start()

while True:
    # Our main loop where we have the server poll for incoming requests
    wsgiServer.update_poll()
    # Maintain DHCP lease
    eth.maintain_dhcp_lease()
    # Could do any other background tasks here, like reading sensors
```

5. Copy **Webserver code** to **code.py** on your RPi Pico and save. Make sure that PC is configured in same subnet 192.168.1.xxx.



## Step 4: Upload and Run

1. Check COMport in [Device Manager] and then open Serial Terminal.

![][link-port]![][link-terminal]

2. When you execute the code, you open Websever and wait.

![][link-webserver_1]

3. If you open the HTML web page and enter 192.168.1.4, you will see the page. In addition, you will see the IP address of the server connected and WIZnet chip.

![][link-webserver_2]![][link-webserver_3]

4. If you press the ON button below, the LED built into the Pico turns on.

![][link-webserver_4]![][link-webserver_5]

5. Turn on LED, Likewise, if you press OFF, the LED turns off.

![][link-webserver_6]



## Attach

Attach a flow that operates through [WIRESHARK](https://www.wireshark.org/#download).

- [HTTP_Server.pcapng](https://github.com/Wiznet/RP2040-HAT-CircuitPython/blob/master/examples/HTTP/Webserver/HTTP_Server.pcapng)




 [**◀ Go to Ethernet example structure**](#ethernet_example_structure)




<!--
Link
-->

[link-tera_term]: https://osdn.net/projects/ttssh2/releases/
[link-hercules]: https://www.hw-group.com/software/hercules-setup-utility
[link-http]: https://github.com/Wiznet/RP2040-HAT-CircuitPython/blob/master/images/HTTP/HTTP_0.jpg



[link-port]:https://github.com/Wiznet/RP2040-HAT-CircuitPython/blob/master/images/HTTP/PORT.jpg
[link-terminal]: https://github.com/Wiznet/RP2040-HAT-CircuitPython/blob/master/images/HTTP/Terminal.jpg



[link-http_0]: https://github.com/Wiznet/RP2040-HAT-CircuitPython/blob/master/images/HTTP/HTTP.png
[link-webserver_1]: https://github.com/Wiznet/RP2040-HAT-CircuitPython/blob/master/images/HTTP/Webserver_1.PNG
[link-webserver_2]: https://github.com/Wiznet/RP2040-HAT-CircuitPython/blob/master/images/HTTP/Webserver_2.PNG
[link-webserver_3]: https://github.com/Wiznet/RP2040-HAT-CircuitPython/blob/master/images/HTTP/Webserver_3.PNG
[link-webserver_4]: https://github.com/Wiznet/RP2040-HAT-CircuitPython/blob/master/images/HTTP/Webserver_4.PNG
[link-webserver_5]: https://github.com/Wiznet/RP2040-HAT-CircuitPython/blob/master/images/HTTP/Webserver_5.PNG
[link-webserver_6]: https://github.com/Wiznet/RP2040-HAT-CircuitPython/blob/master/images/HTTP/Webserver_6.jpg


# WIZnet Ethernet HAT & Raspberry Pi Pico [RP2040]

- [Overview](#overview)

- [CircuitPython Getting Started](#start)

- [Directory Structure](#directory )


<a name="overview"></a>

# :blue_book:Overview

WIZnet W5100S Ethernet Shield includes W5100S chip - hardwired TCP/IP internet controller. The Ethernet Shield is connected to the Raspberry Pi Pico via SPI interface, making it easy to add Ethernet communication ability. Another option is using WIZ810Sio module which is also built on W5100S chip.

![][link-wiznet_pico_]

<a name="start"></a>

# :rocket:CircuitPython Getting Started

Please refer to [getting_stared.md][link-getting_started] for examples usage.
![][link-getting_image]

<a name="directory"></a>

# :black_nib:Directory Structure

``` bash
├─examples
│  ├─Adafruit_IO
│  │  ├─DownLink
│  │  ├─Up&DownLink
│  │  └─UpLink
│  ├─DHCP
│  ├─DNS
│  ├─HTTP
│  │  ├─Webclient
│  │  └─Webserver
│  ├─HTTP_Request
│  ├─Loopback
│  ├─MQTT
│  │  ├─Publish
│  │  ├─PubSub
│  │  └─Subscribe
│  ├─Neopixel
│  ├─Network
│  └─SNTP
└─libraries
    ├─adafruit_bus_device
    ├─adafruit_io
    ├─adafruit_minimqtt
    ├─adafruit_wiznet5k  
    └─adafruit_wsgi
```



<!--
Link
-->

[link-wiznet_pico_]: https://github.com/Wiznet/RP2040-HAT-CircuitPython/blob/master/images/START/WIZnet_PICO_.jpg
[link-getting_image]: https://github.com/Wiznet/RP2040-HAT-CircuitPython/blob/master/images/START/getting_started.png
[link-getting_started]: https://github.com/Wiznet/RP2040-HAT-CircuitPython/blob/master/Ethernet%20Example%20Getting%20Started%20%5BCircuitpython%5D.md


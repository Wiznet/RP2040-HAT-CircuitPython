# How to Downlink Adafruit IO Example

![][link-adafruit_logo_2]



## Step 1: Prepare Software

> The following serial terminal program is required for **Adafruit Downlink** test, download and install from below links.

### &#10004;[**Tera Term**][link-tera_term]  or  &#10004; [**Adafruit IO**][link-adafruit_io]



## Step 2: Prepare hardware

1. Combine WIZnet Ethernet HAT with Raspberry Pi Pico.
2. Connect ethernet cable to Ethernet HAT ethernet port.
3. Connect Raspberry Pi Pico to desktop or laptop using 5 pin micro USB cable.



If you use W5100S-EVB-Pico, you can skip '1. Combine...'



## Step 3: Setup Adafruit IO Downlink Example

> To test the **Adafruit IO Downlink**, minor settings shall be done in code.



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

2. Initialize ethernet interface with DHCP.

```python
eth = WIZNET5K(spi_bus, cs, is_dhcp=True, mac=MY_MAC, debug=False)
```

3. Get [Username] and [Active Key] by referring to the link and add them to the **Secrets**.

```python
secrets = {
    'aio_username' : '*****',  ### Wirte your Username here ###
    'aio_key' : 	 '*****',  ### Write your Active Key here ###
    }
```

4. Create a socket and create a client to access **Adafruit IO** through **MQTT**.

```python
# Initialize MQTT interface with the ethernet interface
MQTT.set_socket(socket, eth)

# Initialize a new MQTT Client object
mqtt_client = MQTT.MQTT(
    broker="io.adafruit.com",
    username=secrets["aio_username"],
    password=secrets["aio_key"],
    is_ssl=False,
)

# Initialize an Adafruit IO MQTT Client
io = IO_MQTT(mqtt_client)
```

5. Register the Callback function and connect to the **Adafruit IO Server through subscription**.

```python
# Set up a callback for the led feed
io.add_feed_callback("led", on_led_msg)

# Connect to Adafruit IO
print("Connecting to Adafruit IO...")
io.connect()

# # Subscribe to all messages on the led feed
io.subscribe("led")
print("Connected to Adafruit !!")

#Random Data Send
while True:
    io.loop()
    #send a new message
```

6. Copy **Adafruit IO Downlink code** to **code.py** on your RPi Pico and save. Make sure that PC is configured in same subnet 192.168.1.xxx.



## Step 4: Upload and Run

**Before starting, check the contents of the link below.**

> [**Getting start Adafruit IO**][link-adafruit_start]



1. Check COMport in [Device Manager] and then open Serial Terminal.

![][link-port]![][link-terminal]



2. Create LED Feed in Adafruit IO to turn on the LED

![][link-adafruit_downlink_2]



3. Based on the feed created, LED button icons are created on the dashboard.

![][link-adafruit_downlink_3]



4. When feeds and icons are connected to each other and "1" is added to the button value, a block in which the value "0" is input is created when ON or OFF is selected.

![][link-adafruit_downlink_4]



5. Run Pico to connect to Adafruit IO.

![][link-adafruit_downlink_1]



6. The LED inside the PICO is lit through the data transmitted from the **Adafruit Server**.

![][link-adafruit_downlink_6]



7. The data that received the "1" data will be received on the Pico board and the LED will turn on.

![][link-adafruit_downlink_7]



## Attach

Attach a flow that operates through [WIRESHARK](https://www.wireshark.org/#download).

- [Adafruit_downlink.pcapng](https://github.com/Wiznet/RP2040-HAT-CircuitPython/blob/master/examples/Adafruit_IO/DownLink/Adafruit_downlink.pcapng)




 [**◀ Go to Ethernet example structure**](#ethernet_example_structure)



<!--
Link
-->

[link-tera_term]: https://osdn.net/projects/ttssh2/releases/
[link-adafruit_io]: https://io.adafruit.com/
[link-adafruit_start]: https://github.com/Wiznet/RP2040-HAT-CircuitPython/blob/master/examples/Adafruit_IO/Getting%20Start%20Adafruit%20IO.md



[link-adafruit_logo_2]: https://github.com/Wiznet/RP2040-HAT-CircuitPython/blob/master/images/Adaruit_io/Adafruit_logo_2.png
[link-port]:https://github.com/Wiznet/RP2040-HAT-CircuitPython/blob/master/images/Adaruit_io/PORT.jpg
[link-terminal]: https://github.com/Wiznet/RP2040-HAT-CircuitPython/blob/master/images/Adaruit_io/Terminal.jpg
[link-adafruit_downlink_1]: https://github.com/Wiznet/RP2040-HAT-CircuitPython/blob/master/images/Adaruit_io/Adafruit_downlink_1.PNG
[link-adafruit_downlink_2]: https://github.com/Wiznet/RP2040-HAT-CircuitPython/blob/master/images/Adaruit_io/Adafruit_downlink_2.PNG
[link-adafruit_downlink_3]: https://github.com/Wiznet/RP2040-HAT-CircuitPython/blob/master/images/Adaruit_io/Adafruit_downlink_3.PNG
[link-adafruit_downlink_4]: https://github.com/Wiznet/RP2040-HAT-CircuitPython/blob/master/images/Adaruit_io/Adafruit_downlink_4.PNG
[link-adafruit_downlink_6]: https://github.com/Wiznet/RP2040-HAT-CircuitPython/blob/master/images/Adaruit_io/Adafruit_downlink_6.PNG
[link-adafruit_downlink_7]: https://github.com/Wiznet/RP2040-HAT-CircuitPython/blob/master/images/Adaruit_io/Adafruit_downlink_7.PNG


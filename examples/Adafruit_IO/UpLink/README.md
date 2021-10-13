# How to Uplink Adafruit IO Example

![][link-adafruit_logo_2]



## Step 1: Prepare Software

> The following serial terminal program is required for **Adafruit Uplink** test, download and install from below links.

### &#10004;[**Tera Term**][link-tera_term]  or  &#10004; [**Adafruit IO**][link-adafruit_io]



## Step 2: Prepare hardware

1. Combine WIZnet Ethernet HAT with Raspberry Pi Pico.
2. Connect ethernet cable to Ethernet HAT ethernet port.
3. Connect Raspberry Pi Pico to desktop or laptop using 5 pin micro USB cable.



If you use W5100S-EVB-Pico, you can skip '1. Combine...'



## Step 3: Setup Adafruit IO Uplink Example

> To test the **Adafruit IO Uplink**, minor settings shall be done in code.



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

3. Get `[Username]` and `[Active Key]` by referring to the link and add them to the **Secrets**.

```python
secrets = {
    'aio_username' : '*****',  ### Wirte your Username here ###
    'aio_key' :  '*****',  ### Write your Active Key here ###
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

5. Connect to Adafruit IO and continue to **send random data** every 5 seconds..

```python
# Connect to Adafruit IO
print("Connecting to Adafruit IO...")
io.connect()

#Random Data Send to Adafurit IO
while True:
    #io.loop()
    #send a new message
    rand = randint(1,100)
    mqtt_client.publish(mqtt_topic, rand)
    print("Random Data %d Sent!" %rand)
    time.sleep(5)
```

6. Copy **Adafruit IO Uplink code** to **code.py** on your RPi Pico and save. Make sure that PC is configured in same subnet 192.168.1.xxx.



## Step 4: Upload and Run

**Before starting, check the contents of the link below.**

[**Getting start Adafruit IO**][link-adafruit_start]



1. Check COMport in [Device Manager] and then open Serial Terminal.

![][link-port]![][link-terminal]



2. First, make a feed. Type Test in your name and create it.

![][link-adafruit_uplink_1]



3. Create a block, and make a line chart that draws a graph.

![][link-adafruit_uplink_2]



4. Connect the feed to make the name, and set the maximum and minimum values.

![][link-adafruit_uplink_3]



5. Run Pico to connect to Adafruit IO.

![][link-adafruit_uplink_4]



6. If you place the generated block on the dashboard, you can see that the chart was created as shown in the picture below.

![][link-adafruit_uplink_5]



7. When Pico is executed, Random data is sent every 5 seconds. The chart is drawn according to the cumulative value of the data.

![][link-adafruit_uplink_6]



## Attach

Attach a flow that operates through [WIRESHARK](https://www.wireshark.org/#download).

- [Adafruit_uplink.pcapng](https://github.com/Wiznet/RP2040-HAT-CircuitPython/blob/master/examples/Adafruit_IO/UpLink/Adafruit_uplink.pcapng)




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
[link-adafruit_uplink_1]: https://github.com/Wiznet/RP2040-HAT-CircuitPython/blob/master/images/Adaruit_io/Adafruit_uplink_1.PNG
[link-adafruit_uplink_2]: https://github.com/Wiznet/RP2040-HAT-CircuitPython/blob/master/images/Adaruit_io/Adafruit_uplink_2.PNG
[link-adafruit_uplink_3]: https://github.com/Wiznet/RP2040-HAT-CircuitPython/blob/master/images/Adaruit_io/Adafruit_uplink_3.PNG
[link-adafruit_uplink_4]: https://github.com/Wiznet/RP2040-HAT-CircuitPython/blob/master/images/Adaruit_io/Adafruit_uplink_4.PNG
[link-adafruit_uplink_5]: https://github.com/Wiznet/RP2040-HAT-CircuitPython/blob/master/images/Adaruit_io/Adafruit_uplink_5.PNG
[link-adafruit_uplink_6]: https://github.com/Wiznet/RP2040-HAT-CircuitPython/blob/master/images/Adaruit_io/Adafruit_uplink_6.PNG




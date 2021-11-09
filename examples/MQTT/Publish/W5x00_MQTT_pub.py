import board
import busio
import digitalio
import time

from adafruit_wiznet5k.adafruit_wiznet5k import *
import adafruit_wiznet5k.adafruit_wiznet5k_socket as socket

import adafruit_minimqtt.adafruit_minimqtt as MQTT

### MQTT Setup ###
# MQTT Topic
# Use this topic if you'd like to connect to a standard MQTT broker
mqtt_topic = 'WIZnetTest'

# MQTT Send Message text
text = "Hello Broker, I'm PICO"

# Set up a MiniMQTT Client
# NOTE: We'll need to connect insecurely for ethernet configurations.
mqtt_client = MQTT.MQTT(
    broker="192.168.1.11",  #setup your PC IP address
    username="rpi-pico",       
    password="wiznet",      
    is_ssl=False,
    socket_pool=None,
    ssl_context=None,
    keep_alive=60,
)
   
#SPI0
SPI0_SCK = board.GP18
SPI0_TX = board.GP19
SPI0_RX = board.GP16
SPI0_CSn = board.GP17

#Reset
W5x00_RSTn = board.GP20

print("Wiznet5k MQTT Test (DHCP)")
# Setup your network configuration below
# random MAC, later should change this value on your vendor ID
MY_MAC = (0x00, 0x01, 0x02, 0x03, 0x04, 0x05)
IP_ADDRESS = (192, 168, 1, 100)
SUBNET_MASK = (255, 255, 255, 0)
GATEWAY_ADDRESS = (192, 168, 1, 1)
DNS_SERVER = (8, 8, 8, 8)

led = digitalio.DigitalInOut(board.GP25)
led.direction = digitalio.Direction.OUTPUT

ethernetRst = digitalio.DigitalInOut(W5x00_RSTn)
ethernetRst.direction = digitalio.Direction.OUTPUT

# For Adafruit Ethernet FeatherWing
cs = digitalio.DigitalInOut(SPI0_CSn)
# For Particle Ethernet FeatherWing
# cs = digitalio.DigitalInOut(board.D5)

spi_bus = busio.SPI(SPI0_SCK, MOSI=SPI0_TX, MISO=SPI0_RX)

# Reset W5500 first
ethernetRst.value = False
time.sleep(1)
ethernetRst.value = True

# # Initialize ethernet interface without DHCP
# eth = WIZNET5K(spi_bus, cs, is_dhcp=False, mac=MY_MAC, debug=False)
# # Set network configuration
# eth.ifconfig = (IP_ADDRESS, SUBNET_MASK, GATEWAY_ ADDRESS, DNS_SERVER)

# Initialize ethernet interface with DHCP
eth = WIZNET5K(spi_bus, cs, is_dhcp=True, mac=MY_MAC, debug=False)

print("Chip Version:", eth.chip)
print("MAC Address:", [hex(i) for i in eth.mac_address])
print("My IP address is:", eth.pretty_ip(eth.ip_address))

# Initialize MQTT interface with the ethernet interface
MQTT.set_socket(socket, eth)

# Connect the client to the MQTT broker.
print("Connecting to Broker...")
mqtt_client.connect()

###MQTT Publisher Run###
while True:
    #mqtt_client.loop()

    #send a new message
    mqtt_client.publish(mqtt_topic, text)
    print("{0} topic send {1} to broker".format(mqtt_topic, text))

    time.sleep(1)

#Disconnected
print("Disconnecting from %s" % mqtt_client.broker)
mqtt_client.disconnect()
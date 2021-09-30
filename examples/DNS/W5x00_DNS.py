import board
import busio
import digitalio
import time

import adafruit_requests as requests
from adafruit_wiznet5k.adafruit_wiznet5k import *
import adafruit_wiznet5k.adafruit_wiznet5k_socket as socket
import adafruit_wiznet5k.adafruit_wiznet5k_dns as dns

##SPI0
SPI0_SCK = board.GP18
SPI0_TX = board.GP19
SPI0_RX = board.GP16
SPI0_CSn = board.GP17

##reset
W5x00_RSTn = board.GP20

print("Wiznet5k Loopback Test (DHCP)")

# Setup your network configuration below
# random MAC, later should change this value on your vendor ID
MY_MAC = (0x00, 0x01, 0x02, 0x03, 0x04, 0x05)
IP_ADDRESS = (192, 168, 1, 11)
SUBNET_MASK = (255, 255, 255, 0)
GATEWAY_ADDRESS = (192, 168, 1, 1)
DNS_SERVER = (8, 8, 8, 8)

led = digitalio.DigitalInOut(board.GP25)
led.direction = digitalio.Direction.OUTPUT

ethernetRst = digitalio.DigitalInOut(W5x00_RSTn)
ethernetRst.direction = digitalio.Direction.OUTPUT

# For Adafruit Ethernet FeatherWing
cs = digitalio.DigitalInOut(SPI0_CSn)

# cs = digitalio.DigitalInOut(board.D5)
spi_bus = busio.SPI(SPI0_SCK, MOSI=SPI0_TX, MISO=SPI0_RX)

# Reset W5500 first
ethernetRst.value = False
time.sleep(1)
ethernetRst.value = True

# Initialize ethernet interface without DHCP
# eth = WIZNET5K(spi_bus, cs, is_dhcp=False, mac=MY_MAC, debug=False)
# Initialize ethernet interface with DHCP
eth = WIZNET5K(spi_bus, cs, is_dhcp=True, mac=MY_MAC, debug=False)

# Set network configuration
# eth.ifconfig = (IP_ADDRESS, SUBNET_MASK, GATEWAY_ADDRESS, DNS_SERVER)

#print information
print("Chip Version:", eth.chip)
print("MAC Address:", [hex(i) for i in eth.mac_address])
print("My IP address is:", eth.pretty_ip(eth.ip_address))

#DNS_Loopup
while True:
    print("DNS Translate : DNS Server        -->> %s" % eth.pretty_ip(eth.get_host_by_name("kns.kornet.net")))  #DNS Domain
    print("DNS Translate : www.google.com    -->> %s" % eth.pretty_ip(eth.get_host_by_name("www.google.com")))  #Google Domain
    print("DNS Translate : www.adafruit.com  -->> %s" % eth.pretty_ip(eth.get_host_by_name("www.adafruit.com")))#adafruit Domain
    print("DNS Translate : wiznet.io         -->> %s" % eth.pretty_ip(eth.get_host_by_name("wiznet.io")))       #Wiznet Domain
    time.sleep(5)
    

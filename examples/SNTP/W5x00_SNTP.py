import board
import busio
import digitalio
import time
import adafruit_requests as requests
from adafruit_wiznet5k.adafruit_wiznet5k import *
import adafruit_wiznet5k.adafruit_wiznet5k_socket as socket
from adafruit_wiznet5k.adafruit_wiznet5k_ntp import NTP
import adafruit_wiznet5k.adafruit_wiznet5k_dns as dns
days = ("Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday")
             
##SPI0
SPI0_SCK = board.GP18
SPI0_TX = board.GP19
SPI0_RX = board.GP16
SPI0_CSn = board.GP17

##reset
W5x00_RSTn = board.GP20

print("Wiznet5k NTP Client ( DHCP)")

# Setup your network configuration below
# random MAC, later should change this value on your vendor ID
MY_MAC = (0x00, 0x01, 0x02, 0xFF, 0xFF, 0xFF)
IP_ADDRESS = (192, 168, 1, 11)
SUBNET_MASK = (255, 255, 255, 0)
GATEWAY_ADDRESS = (192, 168, 1, 1)
DNS_SERVER = (8, 8, 8, 8)
port = 5000
ntp_server_port= 123

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
#eth = WIZNET5K(spi_bus, cs, is_dhcp=False, mac=MY_MAC, debug=False)
# Initialize ethernet interface with DHCP
eth = WIZNET5K(spi_bus, cs, is_dhcp=True, mac=MY_MAC, debug=False)
print("Chip Version:", eth.chip)
print("MAC Address:", [hex(i) for i in eth.mac_address])
print("My IP address is:", eth.pretty_ip(eth.ip_address))

# Initialize a socket for our server
#socket.set_interface(eth)
# Set network configuration
#eth.ifconfig = (IP_ADDRESS, SUBNET_MASK, GATEWAY_ADDRESS, DNS_SERVER)

#NTP
ntpserver_ip = eth.pretty_ip(eth.get_host_by_name("time.google.com"))
print("NTP : %s" % ntpserver_ip)  #DNS Domain
ntp = NTP(iface = eth, ntp_address =ntpserver_ip ,utc=9)
cal = ntp.get_time()
print("The date is %s %d/%d/%d" %(days[cal.tm_wday], cal.tm_mday,cal.tm_mon,cal.tm_year))
print("The time is %d:%02d:%02d" %(cal.tm_hour,cal.tm_min,cal.tm_sec))

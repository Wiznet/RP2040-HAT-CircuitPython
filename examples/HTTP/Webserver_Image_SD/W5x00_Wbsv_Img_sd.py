import os

import board
import busio
import digitalio
import time

## for SDcard

import storage
import adafruit_sdcard

import adafruit_requests as requests
from adafruit_wiznet5k.adafruit_wiznet5k import *
from adafruit_wsgi.wsgi_app import WSGIApp
import adafruit_wiznet5k.adafruit_wiznet5k_wsgiserver as server
import adafruit_wiznet5k.adafruit_wiznet5k_socket as socket

#sd
SD_CS = board.GP9    

# Connect to the card and mount the filesystem.
#sck, mosi, miso
#spi_sd = busio.SPI(board.GP10, board.GP11, board.GP12)
#cs_sd = digitalio.DigitalInOut(SD_CS)
#sdcard = adafruit_sdcard.SDCard(spi_sd, cs_sd, 655360)
#vfs = storage.VfsFat(sdcard)
#storage.mount(vfs, "/sd")
#with open("/sd/test01.txt", "w") as file:
#    file.write("Hello, SD World!\r\n")
#    file.write("This is a test\r\n")
#    file.write("한글 출력 테스트\r\n")
#time.sleep(1)

##SPI0
SPI0_SCK = board.GP18
SPI0_TX = board.GP19
SPI0_RX = board.GP16
SPI0_CSn = board.GP17

##reset
W5x00_RSTn = board.GP20

print("Wiznet5k WebServer Test(DHCP)")

# Setup your network configuration below
# random MAC, later should change this value on your vendor ID
MY_MAC = (0x00, 0x01, 0x02, 0x03, 0x04, 0x05)
IP_ADDRESS = (192, 168, 52, 121)
SUBNET_MASK = (255, 255, 255, 0)
GATEWAY_ADDRESS = (192, 168, 52, 254)
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

print("Chip Version:", eth.chip)
print("MAC Address:", [hex(i) for i in eth.mac_address])
print("My IP address is:", eth.pretty_ip(eth.ip_address))

# Initialize a requests object with a socket and ethernet interface
requests.set_socket(socket, eth)

# Here we create our application, registering the
# following functions to be called on specific HTTP GET requests routes
web_app = WSGIApp()


# Object Size Test Code New!  04.29  
import gc
gc.collect();
start = gc.mem_free()

with open("/sample1.jpg", "r") as f:
    smpng = f.read()
    f.close()

print("Memory Using :", start - gc.mem_free())


with open("/index.html", "r") as f:
    html_string = f.read()
    html_string = html_string.replace("$CHIPNAME",eth.chip)
    html_string = html_string.replace("$IPADDRESS",eth.pretty_ip(eth.ip_address))
    f.close()


#HTTP Request handlers
@web_app.route("/led_on")
def led_on(request):  # pylint: disable=unused-argument
    print("LED on!")
    led.value = True
    return ("200 OK", [], " led on!")
	
@web_app.route("/led_off")
def led_off(request): # pylint: disable=unused-argument
	print("LED off!")
	led.value = False
	return ("200 OK", [], " led off!")

#methods=["POST"]
@web_app.route("/imgsmp")
def imgsmp(request): # pylint: disable=unused-argument
#    headrs = [('Content-Type', 'image/jpeg'), ('Content-Length', 5120)]
#    return ("HTTP/2.0 200 OK\r\nContent-type: image/png; charset=utf-8\r\nContent-Length: 16384", [], [smpng])
    return ("200 OK", [], [smpng])

@web_app.route("/")
def root(request, methods=["POST"]):  # pylint: disable=unused-argument
    print("Root WSGI handler")
    # return ("200 OK", [], ["Root document"])
    return ("HTTP/2.0 200 OK\r\nContent-type: text/html; charset=utf-8\r\nContent-Length: 8192", [], [html_string])

# Here we setup our server, passing in our web_app as the application
server.set_interface(eth)
print(eth.chip)
wsgiServer = server.WSGIServer(80, application=web_app)

print("Open this IP in your browser: ", eth.pretty_ip(eth.ip_address))

# Start the server
wsgiServer.start()

while True:
    # Our main loop where we have the server poll for incoming requests
    wsgiServer.update_poll()
    # Maintain DHCP lease
    eth.maintain_dhcp_lease()
    # Could do any other background tasks here, like reading sensors





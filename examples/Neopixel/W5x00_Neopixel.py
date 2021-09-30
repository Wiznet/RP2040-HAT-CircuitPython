import board
import busio
import digitalio
import time
from adafruit_wiznet5k.adafruit_wiznet5k import *
import adafruit_wiznet5k.adafruit_wiznet5k_socket as socket
import neopixel
 
##SPI0
SPI0_SCK = board.GP18
SPI0_TX = board.GP19
SPI0_RX = board.GP16
SPI0_CSn = board.GP17

##reset
W5x00_RSTn = board.GP20

pixel_pin = board.GP3
num_pixels = 2

print("Wiznet5k SimpleServer Test (DHCP)")
# Setup your network configuration below
# random MAC, later should change this value on your vendor ID
MY_MAC = (0x00, 0x01, 0x02, 0x03, 0x04, 0x05)
IP_ADDRESS = (192, 168, 1, 111)
SUBNET_MASK = (255, 255, 255, 0)
GATEWAY_ADDRESS = (192, 168, 1, 1)
DNS_SERVER = (8, 8, 8, 8)

RED = (255, 0, 0)
YELLOW = (255, 150, 0)
GREEN = (0, 255, 0)
CYAN = (0, 255, 255)
BLUE = (0, 0, 255)
PURPLE = (180, 0, 255)

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
# eth.ifconfig = (IP_ADDRESS, SUBNET_MASK, GATEWAY_ADDRESS, DNS_SERVER)

# Initialize ethernet interface with DHCP
eth = WIZNET5K(spi_bus, cs, is_dhcp=True, mac=MY_MAC, debug=False)

print("Chip Version:", eth.chip)
print("MAC Address:", [hex(i) for i in eth.mac_address])
print("My IP address is:", eth.pretty_ip(eth.ip_address))

pixels = neopixel.NeoPixel(pixel_pin, num_pixels, brightness=0.1, auto_write=False)

# Initialize a socket for our server
socket.set_interface(eth)
server = socket.socket()  # Allocate socket for the server
server_ip = None  # IP address of server
server_port = 5000  # Port to listen on
server.bind((server_ip, server_port))  # Bind to IP and Port
server.listen()  # Begin listening for incoming clients
print("server listen")

conn = None

while True:
    if conn is None:
        conn, addr = server.accept()  # Wait for a connection from a client.
        print("socket connected")
        print(conn, addr)
    else :
        if conn.status in (
            SNSR_SOCK_FIN_WAIT,
            SNSR_SOCK_CLOSE_WAIT,
        ):
            print("socket closed")
            conn.close()
            conn = None
        else :
            # print("socket established", conn.status)
            data = conn.recv()
            if data:
                print(data)
                conn.send(data)  # Echo message back to client
                # expect data format RED example: 255,0,0
                recvStr = data.decode('UTF-8')
                print(recvStr)
                color = recvStr.split(",", 2)
                print(color)
                if len(color) != 3 or not "".join(color).isdigit():
                    pass
                red = int(color[0])
                green = int(color[1])
                blue = int(color[2])
                pixels.fill((red,green,blue))
                pixels.show()

    led.value = not led.value
    time.sleep(1)

print("Done!")

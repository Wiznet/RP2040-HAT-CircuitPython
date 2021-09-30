import board
import busio
import digitalio
import time
from adafruit_wiznet5k.adafruit_wiznet5k import *
import adafruit_wiznet5k.adafruit_wiznet5k_socket as socket
import sys
import os

##SPI0
SPI0_SCK = board.GP18
SPI0_TX = board.GP19
SPI0_RX = board.GP16
SPI0_CSn = board.GP17

##reset
W5x00_RSTn = board.GP20

print("Send the files using Wiznet5k UDP")
# Setup your network configuration below
# random MAC, later should change this value on your vendor ID
MY_MAC = (0x00, 0x01, 0x02, 0x03, 0x04, 0x05)
IP_ADDRESS = (192, 168, 1, 111)
SUBNET_MASK = (255, 255, 255, 0)
GATEWAY_ADDRESS = (192, 168, 1, 1)
DNS_SERVER = (8, 8, 8, 8)
port = 5001
MAX_SIZE = 1024
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
eth = WIZNET5K(spi_bus, cs, is_dhcp=False, mac=MY_MAC, debug=False)
#if eth() != True :
eth.ifconfig = (IP_ADDRESS, SUBNET_MASK, GATEWAY_ADDRESS, DNS_SERVER)


# Initialize a socket for our server
socket.set_interface(eth)
sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)  # Allocate socket for the server
server_ip = '192.168.1.200'  # IP address of server
server_port = 5000  # Port to listen on

print("Chip Version:", eth.chip)
print("MAC Address:", [hex(i) for i in eth.mac_address])
print("My IP address is:", eth.pretty_ip(eth.ip_address))


class file:
    count=0
    
    def __init__(self, filename):
        self.filename = filename


    def sendfile(filename):
        data_trans = 0
        print( filename)
        with open(filename, 'rb') as f :
            try:
                data=f.read() #Read
                data_trans = len(data)    
            except Exception as e:
                print('error!!!! %s' %e)   
        print('Complete transmission data[%s], transmission size[%d]' %(filename, data_trans))
        return data


while True: #Loop
    print('\'/exit\'')

    filename = input('Input the Filename:')

    if filename == '/exit':
        sys.exit()
    socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    sock.bind((eth.pretty_ip(eth.ip_address),port))

    data = file.sendfile(filename)  
    if len(data) > MAX_SIZE:  # If it is longer than the limited length
        cnt = 0
        while(cnt+1)*MAX_SIZE < len(data): #Repeat if shorter than the Total data
            data_tmp = data[cnt*MAX_SIZE:(cnt+1)*MAX_SIZE] #split transmission
            sock.sendto(data_tmp,(server_ip, server_port))
            cnt = cnt +1
        data_tmp = data[cnt*MAX_SIZE:len(data)] # last transmission
        sock.sendto(data_tmp,(server_ip, server_port))
    else :
        sock.sendto(data,(server_ip, server_port))
        

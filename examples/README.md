# pico-W5500
- Add W5500 Ethernet to Raspberry Pi Pico
- Add W5100S Driver code into /lib/adafruit_wiznet5k

## Usage the example codes

1. Open the code.
2. Copy the content to code.py on your RPI Pico board
3. Save & Done :)

## Library

Find and copy adafruit_bus_device & adafruit_requests.mpy file from Adafruit's CircuitPython library bundle matching your version of CircuitPython. Don't copy all files and folder in the library. 
- https://github.com/adafruit/Adafruit_CircuitPython_Bundle/releases/tag/20210409
- Download adafruit-circuitpython-bundle-6.x-mpy-20210409.zip
- Download adafruit-circuitpython-bundle-6.x-mpy-20210813.zip
~~- unzip and find adafruit_requests.mpy.~~

### Used library list - python codes information in /lib folder (updated.2021.08.13)

For SPI communication, adafruit_bus_device (I2C, SPI support)
- https://github.com/adafruit/Adafruit_CircuitPython_BusDevice

Use adafruit_requests.py instead of adafruit_requests.mpy ; because of some changes from Adafruit_CircuitPython_Wiznet5k
- from https://github.com/adafruit/Adafruit_CircuitPython_Requests/blob/main/adafruit_requests.py

For adafruit_wsgi, download from below link.
- https://github.com/adafruit/Adafruit_CircuitPython_WSGI

For adafruit_bus_device, download from below link.
- https://github.com/adafruit/Adafruit_CircuitPython_BusDevice

For adafruit_wiznet5k, download from below link.
- support W5100S chip version : this repo [/lib/adafruit_wiznet5k](https://github.com/bjnhur/pico-W5500/tree/main/lib/adafruit_wiznet5k)
- modify version : https://github.com/bjnhur/Adafruit_CircuitPython_Wiznet5k
- original version : https://github.com/adafruit/Adafruit_CircuitPython_Wiznet5k

For neopixel library,
- https://github.com/adafruit/Adafruit_CircuitPython_NeoPixel

For minimqtt library,
- https://github.com/adafruit/Adafruit_CircuitPython_MiniMQTT

For basic examples, 
- https://github.com/adafruit/circuitpython/tree/main/tests

# This is a simple web server showing
# temperature, pressure and humidity data

import machine
import network
import socket
import time
from machine import Pin, I2C
from BME280.BME280 import BME280

# The web page template
html = """<!DOCTYPE html>
<html>
    <head> 
        <title>Pico W</title>
        <meta http-equiv="refresh" content="30">
    </head>
    <body> 
        <h1>Pico W with BME280 Sensor</h1>
        <h2>
            Temperature: <span style="color:red">%s</span>, 
            Pressure: <span style="color:red">%s</span>, 
            Humidity: <span style="color:red">%s</span>
        </h2>
    </body>
</html>
"""

# show we are alive
led = Pin("LED", machine.Pin.OUT)
led.on()
# start up the wifi connection
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect('router-name-here', 'connection-password-here')

# try to connect
while True:
    if wlan.status() < 0 or wlan.status() >= 3:
        break
    print('Waiting for connection...')
    time.sleep(5)

if wlan.status() != 3:
    print('Cannot connect to the wifi')
    time.sleep(5)
    machine.reset()
else:
    status = wlan.ifconfig()
    print('WLAN established on: ' + status[0]) # you need this address to connect on

# connect to the BME280 sensor on the i2c bus
i2c = I2C(0, sda=Pin(0), scl=Pin(1))
bme = BME280(i2c=i2c)

# create a socket and start listening
try:
    addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1] # port 80
    skt = socket.socket()
    skt.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    skt.bind(addr)
    skt.listen(1)
    print('Web server is now listening on address: ', addr[1])
except Exception as e:
    print('Get connection failed: ', e)
    machine.reset()

#
# flash the led to let the user know we have a connection
for _ in range (5):
    led.off()
    time.sleep(0.5)
    led.on()
    time.sleep(0.5)
led.off()

# listen for connections, respond and loop back for the next one
conn = None
while True:
    try:
        conn, addr = skt.accept()
        led.on() # flash every time we service a request
        print('Request from: ', addr)
        request = conn.recv(1024) # not used, just interesting to see what was sent
        print(request)

        response = html % bme.values

        conn.send('HTTP/1.0 200 OK\nContent-type: text/html\n\n')
        conn.send(response)
        conn.close()
        led.off()

    except Exception as e:
        print('Something broke while serving the page: ', e)
        if conn != None:
            conn.close()
        if skt != None:
            skt.close()
        print('Connection closed')
        break

# restart if something bad happened
machine.reset()

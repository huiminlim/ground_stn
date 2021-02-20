import serial
import time

# Docs: https://pyserial.readthedocs.io/en/latest/shortintro.html

ser = serial.Serial('COM8')
ser.baudrate = 9600
ser.timeout = None

# ser_bytes = ser.readline()
# print(ser_bytes)
while True:
    ser.write(b'cmd\r\n')
    time.sleep(1)

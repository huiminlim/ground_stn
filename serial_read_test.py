import serial

# Docs: https://pyserial.readthedocs.io/en/latest/shortintro.html

ser = serial.Serial('COM8')
ser.baudrate = 9600
while True:
    ser_bytes = ser.readline()
    print(ser_bytes.decode("utf-8").replace("\r\n", ""))

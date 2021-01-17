import serial

# Docs: https://pyserial.readthedocs.io/en/latest/shortintro.html

ser = serial.Serial('COM22')
ser.baudrate = 9600
ser.timeout = (3000)
while True:
    ser_bytes = ser.read(1);
    print(ser_bytes)

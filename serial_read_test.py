import serial
from datetime import datetime

# Docs: https://pyserial.readthedocs.io/en/latest/shortintro.html

ser = serial.Serial('COM8')
ser.baudrate = 115200
ser.timeout = None
count = 0
test = b"UnJS2d0OmjguqcvJZ7yZgFPOlqeGOpK3etVXeIFRrUDhJDVaTkjJgC5mtXCIshBLAz5833PuTGLsCc8VyEsqYJLMsQQw9qmQQPxh1APo1GKJjBAqONgQ1kCe4xWot76NMpA2CSKWEcpNkAA2hH7sq2OTbGwtlOzRUWGGrzqgLCxuR8GJlQFeXRC1cfFTpEDNcizH"
ser_bytes = ser.read(len(b"start\r\n"))
ser.timeout = 10
start = datetime.now()
while True:
    ser_bytes = ser.read(200)
    if ser_bytes != b"" and ser_bytes != b"start\r\n" and ser_bytes != b"end\r\n":

        print(ser_bytes)

        count_str = str(count)

        if ser_bytes == bytes(count_str.zfill(4), 'ascii') + test:
            print(f"byte {count}: Match")
            print()
        else:
            print(f"byte {count}: Not match")
            print()
        count = count + 1

    elif ser_bytes == b"end\r\n":
        print(f"Time elapsed: {datetime.now()-start}")
        break

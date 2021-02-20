import sys
import serial
from multiprocessing import Process, Pipe


# Function to call in process to collect beacons from TT&C
def handle_incoming_beacons(serial_ttnc_obj, main_pipe):
    pass


# Main function to control all the ground station process transition in Mission Mode Diagram
def main():

    # Initialize serial ports for TT&C transceiver
    ttnc_port = input("Enter COM port for TT&C transceiver: ")
    serial_ttnc = serial.Serial(ttnc_port, 9600, timeout=10)

    # Create pipes to communicate with beacon process
    conn_process_beacon, conn_main_process = Pipe(duplex=True)

    # Initialize serial ports for payload transceiver
    # payload_port = input("Enter COM port for Payload transceiver: ")
    # serial_payload = serial.Serial(payload_port, 115200, timeout=None)

    # Enter Autonomous mode to wait for beacons
    process_beacon_collection = Process(
        target=handle_incoming_beacons, args=(serial_ttnc, conn_process_beacon, ), daemon=True)
    # process_beacon_collection.start()

    run_flag = True
    try:
        while run_flag:

            # Initial begin
            print()
            print("---- GROUND STATION ----")
            init_response = input("To begin, enter [Y]... ")
            if init_response.lower() == 'y':
                print()
                pass
            else:
                print()
                print("Exiting script...")
                break

            # Carry on running script

            pass
    except KeyboardInterrupt:
        run_flag = False

    # serial_payload.close()
    serial_ttnc.close()

    conn_main_process.close()
    conn_process_beacon.close()

    # No need to close process -- daemon set
    # process_beacon_collection.close()

    print("Terminated script")
    sys.exit()


if __name__ == "__main__":
    main()

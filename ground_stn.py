import sys
import serial
import time
from multiprocessing import Process, Pipe

# Note: Run this code only on Ubuntu WSL to allow multiprocessing
# https://icircuit.net/accessing-com-port-from-wsl/2704


# Function to call in process to collect beacons from TT&C
def handle_incoming_beacons(serial_ttnc_obj, main_pipe):
    while True:
        # Check if pipes have anything
        if main_pipe.poll(0.2) == True:
            print("Pipes say something, leave now")
            main_pipe.recv()
            break


# Main function to control all the ground station process transition in Mission Mode Diagram
def main():

    # Internal function to get help message
    def get_help_message():
        msg = ""
        msg = msg + "To transition ground station into these modes, enter commands: " + "\n"
        msg = msg + "Contact mode: [C] " + "\n"
        msg = msg + "Downlink mode: [D] " + "\n"
        msg = msg + "Command entered: "
        return msg

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
        target=handle_incoming_beacons, args=(serial_ttnc, conn_process_beacon))
    process_beacon_collection.daemon = True

    run_flag = True
    try:
        while run_flag:

            # Initial begin
            print()
            print("---- GROUND STATION ----")
            init_response = input("To begin, enter [Y]... ")
            if init_response.lower() == 'y':
                # Carry on running script
                print()
                pass
            else:
                print()
                print("Exiting script...")
                break

            # Begin Autonomous Mode
            print("Entering Autonomous Mode...")
            print()
            process_beacon_collection.start()

            # Wait for trigger to enter other modes
            while run_flag:
                print("---- WAITING FOR COMMANDS ----")
                cmd = input(get_help_message())
                if cmd.lower() == 'c' or cmd.lower() == 'd':
                    conn_main_process.send("stop")
                    process_beacon_collection.join()
                    run_flag = False

                pass

            pass
    except KeyboardInterrupt:
        run_flag = False

    # serial_payload.close()
    serial_ttnc.close()

    conn_main_process.close()
    conn_process_beacon.close()

    print("Terminated script")
    sys.exit()


if __name__ == "__main__":
    main()

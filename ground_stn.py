from multiprocessing import Process, Pipe
from CCSDS_util import *
import sys
import time
import serial

# Note: Run this code only on Ubuntu WSL to allow multiprocessing
# https://icircuit.net/accessing-com-port-from-wsl/2704


def handle_contact_mode(serial_ttnc_obj):
    def get_help_message():
        msg = "" + '\n'
        msg = msg + "Enter telecommand type - " + '\n'
        msg = msg + "OBC HK Request     -   [1]" + '\n'
        msg = msg + "EPS HK Request     -   [2]" + '\n'
        msg = msg + "ADCS HK Request    -   [3]" + '\n'
        msg = msg + "TT&C HK Request    -   [4]" + '\n'
        msg = msg + "Payload HK Request -   [5]" + '\n'
        msg = msg + "Mission Command    -   [11]" + '\n'
        msg = msg + "Downlink Command   -   [21]" + '\n'
        return msg

    ccsds_telecommand = bytearray(0)

    print(get_help_message())
    cmd = int(input())

    print("Timestamp format: [DD-MM-YYYY-hh-mm-ss]")
    if cmd >= 1 and cmd <= 5:
        print("---- HK DATA REQUEST ----")
        timestamp_query_start = input(
            "Enter start timestamp to query for data: ")
        timestamp_query_end = input("Enter end timestamp to query for data: ")

        # print(timestamp_query_start, timestamp_query_end)

    elif cmd == 11:
        print("---- MISSION COMMAND ----")
        timestamp_start_mission = input("Enter timestamp to start mission: ")
        num_images = input("Enter number of images to capture: ")
        interval = input("Enter time interval between captures: ")

        # print(timestamp_start_mission, num_images, interval)

    elif cmd == 21:
        print("---- DOWNLINK COMMAND ----")
        timestamp_start_mission = input("Enter timestamp to start mission: ")
        timestamp_query_downlink_start = input(
            "Enter start timestamp to query for mission: ")
        timestamp_query_downlink_end = input(
            "Enter end timestamp to query for mission: ")

        # print(timestamp_start_mission, timestamp_query_downlink_start,
        #       timestamp_query_downlink_end)


# Function to call in process to collect beacons from TT&C
def handle_incoming_beacons(serial_ttnc_obj, main_pipe):

    # Pretty print beacon data
    def pretty_print_beacon(decoded_beacon):
        print()
        for field, field_dict in decoded_beacon.items():
            print(f"---- {field} ----")
            print("\n".join("{:<30} {}".format(k, v)
                            for k, v in field_dict.items()))
        print()

    while True:
        # Check if pipes have anything
        if main_pipe.poll() == True:
            print("Pipes say something before process leave now")
            main_pipe.recv()
            break

        # Wait to receive beacons
        ccsds_beacon_bytes = serial_ttnc_obj.read(CCSDS_BEACON_LEN_BYTES)
        if ccsds_beacon_bytes:
            decoded_ccsds_beacon = CCSDS_beacon_decoder(ccsds_beacon_bytes)
            pretty_print_beacon(decoded_ccsds_beacon)


# Main function to control all the ground station process transition in Mission Mode Diagram
def main():

    # Internal function to get help message
    def get_help_message():
        msg = ""
        msg = msg + "To transition ground station into these modes, enter commands: " + "\n"
        msg = msg + "Contact mode: [C] " + "\n"
        msg = msg + "Downlink mode: [D] " + "\n"
        msg = msg + "Terminate Script: [Z] " + "\n"
        msg = msg + "Display this help message: [H]" + "\n"
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
        target=handle_incoming_beacons, args=(serial_ttnc, conn_process_beacon), daemon=True)

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
            print("---- WAITING FOR COMMANDS ----")
            print(get_help_message())

            while run_flag:
                cmd = input()
                print()

                if cmd.lower() == 'h':
                    print(get_help_message())

                if cmd.lower() == 'c':

                    # Stop beacon receiving process
                    conn_main_process.send("stop")
                    process_beacon_collection.join()

                    # Start contact mode process
                    print("Start Contact mode process")
                    handle_contact_mode(serial_ttnc)

                    # Resume beacon collection after contact mode process ends
                    process_beacon_collection = Process(
                        target=handle_incoming_beacons, args=(serial_ttnc, conn_process_beacon), daemon=True)
                    process_beacon_collection.start()
                    print("Restart beacon collection process")

                if cmd.lower() == 'd':
                    pass

                if cmd.lower() == 'z':
                    conn_main_process.send("stop")
                    process_beacon_collection.join()
                    run_flag = False
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

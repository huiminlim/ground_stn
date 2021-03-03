from apscheduler.schedulers.background import BackgroundScheduler
from multiprocessing import Process, Pipe
from datetime import datetime, timedelta
from downlink_server import *
from CCSDS_util import *
import serial
import sys


# Note: Run this code only on Ubuntu WSL to allow multiprocessing
# https://icircuit.net/accessing-com-port-from-wsl/2704


def handle_contact_mode(serial_ttnc_obj):
    def get_help_message():
        msg = "" + '\n'
        msg = msg + "Enter telecommand type - " + '\n'
        msg = msg + "OBC HK Request                  -   [1]" + '\n'
        msg = msg + "EPS HK Request                  -   [2]" + '\n'
        msg = msg + "ADCS HK Request                 -   [3]" + '\n'
        msg = msg + "TT&C HK Request                 -   [4]" + '\n'
        msg = msg + "Payload HK Request              -   [5]" + '\n'
        msg = msg + "Mission + Downlink Command      -   [11]" + '\n'
        return msg

    def process_timestamp(ts_str):
        # Process timestamp to datetime object
        # Format: [DD-MM-YYYY-hh-mm-ss]
        ls_ts = ts_str.split('-')
        ls_ts = [int(s) for s in ls_ts]

        return datetime(year=ls_ts[2], month=ls_ts[1], day=ls_ts[0], hour=ls_ts[3], minute=ls_ts[4], second=ls_ts[5])

    try:
        ccsds_telecommand = bytearray(0)

        print(get_help_message())
        cmd = int(input())

        if cmd > 5 and cmd != 11 and cmd != 21:
            print("Telecommand type not recognized")
            return

        print("Timestamp format: [DD-MM-YYYY-hh-mm-ss]")
        if cmd >= 1 and cmd <= 5:
            print("---- HK DATA REQUEST ----")
            timestamp_query_start = input(
                "Enter start timestamp to query for data: ")
            timestamp_query_end = input(
                "Enter end timestamp to query for data: ")

            ccsds_telecommand = CCSDS_create_HK_telecommand(
                cmd, timestamp_query_start, timestamp_query_end)

        elif cmd == 11:
            print("---- MISSION + DOWNLINK COMMAND ----")
            timestamp_start_mission = input(
                "Enter timestamp to start mission: ")

            num_images = input("Enter number of images to capture: ")
            num_images = int(num_images)

            interval = input("Enter time interval between captures (ms): ")
            interval = int(interval)

            timestamp_start_downlink = input(
                "Enter timestamp to start mission: ")

            timestamp_query_downlink_start = input(
                "Enter start timestamp to query for mission: ")

            timestamp_query_downlink_end = input(
                "Enter end timestamp to query for mission: ")

            ccsds_telecommand = CCSDS_create_mission_downlink_telecommand(
                cmd, timestamp_start_mission, num_images, interval, timestamp_start_downlink, timestamp_query_downlink_start, timestamp_query_downlink_end)

        print("Sending CCSDS telecommand...")
        # print(ccsds_telecommand)
        # print(f"length {len(ccsds_telecommand)}")

        TELECOMMAND_PACKET_LEN_BYTES = 38
        while len(ccsds_telecommand) < TELECOMMAND_PACKET_LEN_BYTES:
            ccsds_telecommand = ccsds_telecommand + b'B'

        # Add fake header
        ccsds_telecommand = b'A' + ccsds_telecommand

        print(ccsds_telecommand)
        print(f"length {len(ccsds_telecommand)}")

        serial_ttnc_obj.write(ccsds_telecommand)
        print("Sending done...")

        timestamp = None

        # Await downlink data
        if cmd >= 1 and cmd <= 5:
            print("TO DO: Await HK data")

        if cmd == 11:
            timestamp = process_timestamp(timestamp_start_downlink)

        return cmd, timestamp

    except Exception as ex:
        print(ex)
        pass


# Function to call in process to collect beacons from TT&C
def handle_incoming_beacons(serial_ttnc_obj, main_pipe):

    # Reduce print clutter on terminal
    VERBOSE_MODE = 1

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
            data = main_pipe.recv()
            if data == "stop":
                print("Pipes say stop")
                # main_pipe.recv()
                break
            if data == 'verbose on':
                VERBOSE_MODE = 1
            if data == 'verbose off':
                VERBOSE_MODE = 0

        # Wait to receive beacons
        ccsds_beacon_bytes = serial_ttnc_obj.read(CCSDS_BEACON_LEN_BYTES)
        if ccsds_beacon_bytes:
            decoded_ccsds_beacon = CCSDS_beacon_decoder(ccsds_beacon_bytes)
            if VERBOSE_MODE == 0:
                pretty_print_beacon(decoded_ccsds_beacon)


# Main function to control all the ground station process transition in Mission Mode Diagram
def main():

    # Internal function to get help message
    def get_help_message():
        msg = ""
        msg = msg + "To transition ground station into these modes, enter commands: " + "\n"
        msg = msg + "Contact mode:                      [C] " + "\n"
        # msg = msg + "Downlink mode: [D] " + "\n"
        msg = msg + "Keep beacons quiet:                [Q] " + "\n"
        msg = msg + "Turn on beacons:                   [U] " + "\n"
        msg = msg + "Terminate Script:                  [Z] " + "\n"
        msg = msg + "Display this help message:         [H]" + "\n"
        return msg

    # Initialize serial ports for TT&C transceiver
    ttnc_port = input("Enter COM port for TT&C transceiver: ")
    serial_ttnc = serial.Serial(ttnc_port, 9600, timeout=10)

    # Create pipes to communicate with beacon process
    conn_process_beacon, conn_main_process = Pipe(duplex=True)

    # Initialize serial ports for payload transceiver
    payload_port = input("Enter COM port for Payload transceiver: ")
    serial_payload = serial.Serial(payload_port, 115200, timeout=None)

    # Initialize background scheduler for Downlink task
    scheduler = BackgroundScheduler()
    scheduler.start()

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
                choice = input()
                print()

                if choice.lower() == 'h':
                    print(get_help_message())

                elif choice.lower() == 'c':

                    # Stop beacon receiving process
                    conn_main_process.send("stop")
                    process_beacon_collection.join()

                    # Start contact mode process
                    print("Start Contact mode process")
                    telecommand_type, ts = handle_contact_mode(serial_ttnc)

                    # Schedule downlink task
                    if telecommand_type == 21:
                        print(ts)

                        # Subtract 2 mins from time stamp
                        ts = ts - timedelta(minutes=2)
                        print(ts)

                        scheduler.add_job(
                            handle_downlink_task, next_run_time=ts, args=[serial_payload])
                        pass

                    # Resume beacon collection after contact mode process ends
                    print("Restart beacon collection process")
                    print()
                    process_beacon_collection = Process(
                        target=handle_incoming_beacons, args=(serial_ttnc, conn_process_beacon), daemon=True)
                    process_beacon_collection.start()

                elif choice.lower() == 'q':
                    print("Verbose mode now\n")
                    conn_main_process.send("verbose on")
                    pass

                elif choice.lower() == 'u':
                    print("Verbose mode off\n")
                    conn_main_process.send("verbose off")
                    pass

                elif choice.lower() == 'z':
                    conn_main_process.send("stop")
                    process_beacon_collection.join()
                    run_flag = False

                else:
                    print("Command not found...")
                    print()

    except KeyboardInterrupt:
        run_flag = False

    serial_payload.close()
    serial_ttnc.close()

    conn_main_process.close()
    conn_process_beacon.close()

    print("Terminated script")
    sys.exit()


if __name__ == "__main__":
    main()

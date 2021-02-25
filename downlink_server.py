import serial
import subprocess
from datetime import datetime

# Docs: https://pyserial.readthedocs.io/en/latest/shortintro.html


CHUNK_SIZE = 176
BATCH_SIZE = 300

TELEMETRY_PACKET_TYPE_DOWNLINK_START = 30
TELEMETRY_PACKET_TYPE_DOWNLINK_PACKET = 31

TELEMETRY_PACKET_SIZE_DOWNLINK_START = 18  # Bytes
TELEMETRY_PACKET_SIZE_DOWNLINK_PACKET = 198  # Exclude crc


def handle_downlink_task(ser):
    received_batches = []

    total_chunks_expected = 0
    total_bytes_retrieved = 0
    current_image = 0
    total_images = 1

    while current_image <= total_images:
        # Read in a start CCSDS packet
        print("Waiting for start packet")
        ser_bytes = ser.read(TELEMETRY_PACKET_SIZE_DOWNLINK_START)
        ser.timeout = 5

        total_images = int(ser_bytes[7])
        current_image = int(ser_bytes[8])
        curr_img_total_bytes_retrieved = int.from_bytes(ser_bytes[9:12], 'big')
        curr_img_total_chunks_expected = int.from_bytes(
            ser_bytes[12:15], 'big')
        total_batch_expected = int.from_bytes(ser_bytes[15:18], 'big')

        transfer_start = datetime.now()

        # Receive batches of chunks
        batch_counter = 1
        while batch_counter <= total_batch_expected:

            print(
                f"BATCH READ: Batch {batch_counter} of {total_batch_expected}")

            # Read in batch
            packets_in_batch = batch_read(
                ser, batch_counter, total_batch_expected)

            # received_packets = received_packets + packets_in_batch
            received_batches.append(packets_in_batch)

            batch_counter = batch_counter + 1

        transfer_end = datetime.now()
        elapsed_time = transfer_end - transfer_start
        print(f"Time elapsed: {elapsed_time}")

        # Unravel all batches
        received_packets = []
        for batch in received_batches:
            for packet in batch:
                received_packets.append(packet)

        # Strip CCSDS headers
        # Reassemble into compressed file
        with open(f"out_{current_image}.gz", "wb") as f:
            for packet in received_packets:
                f.write(ccsds_decode_downlink_packets(packet))
            f.close()

        # Call this in linux/bash environment only
        # subprocess.call('./decode.sh out.gz',
        #                 stdout=subprocess.DEVNULL, shell=True)
        ser.timeout = 50
    print("Done... Return to main task")


def ccsds_decode_downlink_packets(chunk):
    return chunk[22:]


def batch_read(serial_obj, current_batch, total_batch):
    chunks_arr = []
    chunks_count = 0

    while True:
        ser_bytes = serial_obj.read(TELEMETRY_PACKET_SIZE_DOWNLINK_PACKET)
        chunks_count = chunks_count + 1
        print(f"Chunk {chunks_count} of {BATCH_SIZE} of size {len(ser_bytes)}")
        chunks_arr.append(ser_bytes)

        # Not the final batch and batch read completely
        if chunks_count == BATCH_SIZE and current_batch < total_batch:
            break

        # Final batch and completed reading all
        if current_batch == total_batch and ser_bytes == b'':
            break

        # Final batch and all chunks in batch are full (edge case)
        if current_batch == total_batch and chunks_count == BATCH_SIZE and len(ser_bytes) > 0:
            break

    print()

    return chunks_arr

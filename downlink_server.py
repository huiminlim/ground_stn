from datetime import datetime

# Docs: https://pyserial.readthedocs.io/en/latest/shortintro.html


CHUNK_SIZE = 179
BATCH_SIZE = 200

TELEMETRY_PACKET_TYPE_DOWNLINK_START = 30
TELEMETRY_PACKET_TYPE_DOWNLINK_PACKET = 31

TELEMETRY_PACKET_SIZE_DOWNLINK_START = 13  # Bytes
TELEMETRY_PACKET_SIZE_DOWNLINK_PACKET = 192  # Exclude crc


def handle_downlink_task(ser):
    files_buffer = []

    received_batches = []

    while True:
        # Read in a start CCSDS packet
        print("Waiting for start packet")
        ser_bytes = ser.read(TELEMETRY_PACKET_SIZE_DOWNLINK_START)

        if ser_bytes == b"":
            break

        ser.timeout = 5
        total_batch_expected = int.from_bytes(ser_bytes[10:], 'big')

        print(f"Total batches: {total_batch_expected}")

        transfer_start = datetime.now()
        # Receive batches of chunks
        batch_counter = 1
        while batch_counter <= total_batch_expected:
            print(
                f"BATCH READ: Batch {batch_counter} of {total_batch_expected}")

            # Read in batch
            packets_in_batch = batch_read(
                ser, batch_counter, total_batch_expected)
            received_batches.append(packets_in_batch)
            batch_counter = batch_counter + 1
        transfer_end = datetime.now()
        elapsed_time = transfer_end - transfer_start
        print(f"Time elapsed: {elapsed_time}")

        # Store list of batches in buffer for processing at end of transfer
        files_buffer.append(received_batches)

        # Wait for a long time before next start packet comes
        ser.timeout = 30

    # Unravel all images received
    current_image = 1
    for received_batches in files_buffer:
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
        current_image = current_image + 1

    print("Done... Return to main task")


def ccsds_decode_downlink_packets(chunk):
    return chunk[13:]


def batch_read(serial_obj, current_batch, total_batch):
    chunks_arr = []
    chunks_count = 0

    while True:
        ser_bytes = serial_obj.read(TELEMETRY_PACKET_SIZE_DOWNLINK_PACKET)

        chunks_count = chunks_count + 1
        print(f"Chunk {chunks_count} of {BATCH_SIZE} of size {len(ser_bytes)}")
        chunks_arr.append(ser_bytes)

        # print(ser_bytes)
        # print()

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

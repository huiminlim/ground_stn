CCSDS_BEACON_LEN_BYTES = 38

# Sequence number of the telecommand packet
TELECOMMAND_PACKET_COUNT = 0


# Function to parse CCSDS packet header
def CCSDS_parse_packet_header(header):
    version_number = header[0] >> 5
    type_indicator = (header[0] >> 4) & 0b1

    secondary_header_flag = (header[0] >> 3) & 0b1

    application_id = ((header[0] & 0b11) << 11) | header[1]
    group_flags = header[2] >> 6
    source_seq_count = ((header[2] & 0b00111111) << 8) | header[3]

    packet_length = (header[4] << 8) | header[5]

    ret_header = {'Version Number': version_number, 'Type Indicator': type_indicator,
                  'Secondary Header Flag': secondary_header_flag, 'Application ID': application_id,
                  'Group Flags': group_flags, 'Source Sequence Count': source_seq_count,
                  'Packet length': packet_length}
    return ret_header


def CCSDS_beacon_decoder(beacon_bytes):

    def parse_beacon_telemetry_type(telemetry_type_field):
        return {'Telemetry ID': telemetry_type_field}

    def parse_beacon_ttnc_field(ttnc_field):

        # Beacon flag -- Not in used
        # beacon_flag = ((ttnc_field[0] >> 7) == 1)

        # Decode mode
        mode_lookup = {0: 'FU1', 1: 'FU2', 2: 'FU3', 3: 'FU4'}
        mode_bits = (ttnc_field[0] & 0b01100000) >> 5
        mode = mode_lookup.get(mode_bits)

        # Decode baud
        baud_lookup = {0: '1200', 1: '2400', 2: '4800', 3: '9600',
                       4: '19200', 5: '38400', 6: '57600', 7: '115200'}
        baud_bits = (ttnc_field[0] & 0b00011100) >> 2
        baud = baud_lookup.get(baud_bits)

        # Channel
        channel_bits = ((ttnc_field[0] & 0b00000011)
                        << 5) | (ttnc_field[1] >> 3)
        channel = str(int(f'{channel_bits:#0}'))

        # Transmit Power
        tx_power_lookup = {0: '-1', 1: '2', 2: '5',
                           3: '8', 4: '11', 5: '14', 6: '17', 7: '20'}
        tx_power_bits = (ttnc_field[1] & 0b111)
        tx_power = tx_power_lookup.get(tx_power_bits)

        # ret_ttnc = {'Beacon Flag': beacon_flag, 'Transmission Mode': mode,
        #             'Baud Rate': baud, 'Channel': channel, 'Transmit Power': tx_power}

        ret_ttnc = {'Transmission Mode': mode, 'Baud Rate': baud,
                    'Channel': channel, 'Transmit Power': tx_power}

        return ret_ttnc

    def parse_beacon_adcs_field(adcs_field):
        # Decode gx
        gx = int.from_bytes(adcs_field[0:2], byteorder='big', signed=True)

        # Decode gy
        gy = int.from_bytes(adcs_field[2:4], byteorder='big', signed=True)

        # Decode gz
        gz = int.from_bytes(adcs_field[4:6], byteorder='big', signed=True)

        # Decode mx
        mx = int.from_bytes(adcs_field[6:8], byteorder='big', signed=True)

        # Decode my
        my = int.from_bytes(adcs_field[8:10], byteorder='big', signed=True)

        # Decode mz
        mz = int.from_bytes(
            adcs_field[10:12], byteorder='big', signed=True)

        ret_adcs = {'gx': gx, 'gy': gy, 'gz': gz,
                    'mx': mx, 'my': my, 'mz': mz}
        return ret_adcs

    def parse_beacon_eps_field(eps_field):
        temp_int = int.from_bytes(
            eps_field[0:3], byteorder='big', signed=True)
        temp = temp_int / 100

        reserved = int.from_bytes(
            eps_field[3:6], byteorder='big', signed=True)

        return {'Temperature': temp, 'Reserved': reserved}

    def parse_beacon_payload_field(payload_field):
        r1 = payload_field[0]
        r2 = payload_field[1]
        r3 = payload_field[2]
        r4 = payload_field[3]

        ret_payload = {'Reserved byte 1': r1, 'Reserved byte 2': r2,
                       'Reserved byte 3': r3, 'Reserved byte 4': r4}
        return ret_payload

    def parse_beacon_timestamp_field(timestamp_field):
        DD = timestamp_field[0]
        MM = timestamp_field[1]
        YYYY = int.from_bytes(
            timestamp_field[2:4], byteorder='big', signed=False)
        hh = timestamp_field[4]
        mm = timestamp_field[5]
        ss = timestamp_field[6]

        ret_timestamp = {"DD": DD, "MM": MM,
                         "YYYY": YYYY, "hh": hh, "mm": mm, "ss": ss}
        return ret_timestamp

    header = beacon_bytes[0:6]
    ret = {'Header': CCSDS_parse_packet_header(header),
           'Telemetry Packet Type': parse_beacon_telemetry_type(beacon_bytes[6]),
           'TT&C': parse_beacon_ttnc_field(beacon_bytes[7:9]),
           'ADCS': parse_beacon_adcs_field(beacon_bytes[9:21]),
           'EPS': parse_beacon_eps_field(beacon_bytes[21:27]),
           'Payload': parse_beacon_payload_field(beacon_bytes[27:31]),
           'Timestamp': parse_beacon_timestamp_field(beacon_bytes[31:])}
    return ret


# --------------------------------------------------------------------

# Function creates a CCSDS header
# Takes in length (in terms of bytes) of the ccsds packet
def CCSDS_create_packet_header(data_field_byte_len):
    global TELECOMMAND_PACKET_COUNT

    # Abstract header as 6 bytes
    header = bytearray(0)  # octet 1, 2, ..., 6

    octet = 0b0

    # Version number
    octet = octet << 3 | 0b000

    # # Packet identification
    # # @Type indicator -- Set to 0 to indicate telemetry packet
    octet = octet << 1 | 0b0

    # # @Packet Secondary Header Flag -- Set to 0 to indicate that secondary header not present
    octet = octet << 1 | 0b0

    # # @Application Process ID
    # # Defines the process onboard that is sending the packet --> TBC
    octet = octet << 11 | 0b10

    header = header + octet.to_bytes(2, 'big')

    octet = 0b0

    # # Packet Sequence Control
    # # @Grouping packets -- No grouping so set to 0
    octet = octet << 2 | 0b11

    # # @Source Sequence Count
    # # Sequence number of packet modulo 16384
    octet = octet << 14 | TELECOMMAND_PACKET_COUNT
    TELECOMMAND_PACKET_COUNT = TELECOMMAND_PACKET_COUNT + 1

    header = header + octet.to_bytes(2, 'big')

    octet = 0b0

    # # Packet Data Length
    # In terms of octets
    # Total number of octets in packet data field - 1
    octet = octet << 16 | (data_field_byte_len - 1)

    header = header + octet.to_bytes(2, 'big')

    return header


# --- TELECOMMAND PACKET CREATION ---
# Process [DD-MM-YYYY-hh-mm-ss] to bytearray
def CCSDS_process_timestamp(timestamp):
    ret = bytearray(0)
    ts_list = [int(s) for s in timestamp.split('-')]

    # DD
    ret = ret + ts_list[0].to_bytes(1, 'big')

    # MM
    ret = ret + ts_list[1].to_bytes(1, 'big')

    # YYYY
    ret = ret + ts_list[2].to_bytes(2, 'big')

    # hh
    ret = ret + ts_list[3].to_bytes(1, 'big')

    # mm
    ret = ret + ts_list[4].to_bytes(1, 'big')

    # ss
    ret = ret + ts_list[5].to_bytes(1, 'big')

    return ret


# Create CCSDS HK telecommand
def CCSDS_create_HK_telecommand(telecommand_type, timestamp_start_query, timestamp_end_query):
    packet_field = bytearray(0)

    # Create the other fields in packet first
    packet_field = packet_field + telecommand_type.to_bytes(1, 'big')
    packet_field = packet_field + \
        CCSDS_process_timestamp(timestamp_start_query)
    packet_field = packet_field + CCSDS_process_timestamp(timestamp_end_query)

    # Create header
    header = CCSDS_create_packet_header(len(packet_field))

    # Return appended packet
    return header + packet_field


def CCSDS_create_mission_telecommand(telecommand_type, timestamp_start_mission, num_images, interval):
    packet_field = bytearray(0)

    # Create the other fields in packet first
    packet_field = packet_field + telecommand_type.to_bytes(1, 'big')
    packet_field = packet_field + \
        CCSDS_process_timestamp(timestamp_start_mission)
    packet_field = packet_field + num_images.to_bytes(1, 'big')
    packet_field = packet_field + interval.to_bytes(2, 'big')

    # Create header
    header = CCSDS_create_packet_header(len(packet_field))

    # Return appended packet
    return header + packet_field


def CCSDS_create_downlink_telecommand(telecommand_type, timestamp_start_downlink, timestamp_start_query, timestamp_end_query):
    packet_field = bytearray(0)

    # Create the other fields in packet first
    packet_field = packet_field + telecommand_type.to_bytes(1, 'big')
    packet_field = packet_field + \
        CCSDS_process_timestamp(timestamp_start_downlink)
    packet_field = packet_field + \
        CCSDS_process_timestamp(timestamp_start_query)
    packet_field = packet_field + \
        CCSDS_process_timestamp(timestamp_end_query)

    # Create header
    header = CCSDS_create_packet_header(len(packet_field))

    # Return appended packet
    return header + packet_field


def CCSDS_create_mission_downlink_telecommand(telecommand_type, timestamp_start_mission, num_images, interval, timestamp_start_downlink, timestamp_start_query, timestamp_end_query):
    packet_field = bytearray(0)

    # Create the other fields in packet first
    packet_field = packet_field + telecommand_type.to_bytes(1, 'big')

    # Mission related
    packet_field = packet_field + \
        CCSDS_process_timestamp(timestamp_start_mission)
    packet_field = packet_field + num_images.to_bytes(1, 'big')
    packet_field = packet_field + interval.to_bytes(2, 'big')

    # Downlink related
    packet_field = packet_field + \
        CCSDS_process_timestamp(timestamp_start_downlink)
    packet_field = packet_field + \
        CCSDS_process_timestamp(timestamp_start_query)
    packet_field = packet_field + \
        CCSDS_process_timestamp(timestamp_end_query)

    # Create header
    header = CCSDS_create_packet_header(len(packet_field))

    # Return appended packet
    return header + packet_field

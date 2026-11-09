from firmware_parser import FirmwareParser
from serial_handler import SerialHandler

from protocol import (
    build_start_update_packet,
    build_data_packet,
    build_end_update_packet,
    FIRMWARE_CHUNK_SIZE
)

import sys

FIRMWARE_VERSION = 0x01000002  # Version 1.0.2


def test_crc_corruption(serial_handler, firmware):

    MAX_RETRIES = 3

    # Keep original firmware unchanged
    original_data = firmware.firmware_data

    # Create a separate corrupted copy
    corrupted_data = bytearray(original_data)

    # Corrupt one byte
    corrupted_data[100] ^= 0x01

    print("\nCRC CORRUPTION TEST")
    print("-------------------")
    print("Original firmware size:", len(original_data))
    print("Corrupted byte offset: 100")

    # Step 1: Send START_UPDATE with ORIGINAL firmware
    print("\nStarting firmware update...")

    start_packet = build_start_update_packet(
        original_data,
        FIRMWARE_VERSION
    )

    serial_handler.send(start_packet)

    if not serial_handler.receive_start_response():
        print("START_UPDATE failed!")
        return False

    print("STM32 accepted firmware update.")

    # Step 2: Transfer CORRUPTED firmware
    offset = 0

    while offset < len(corrupted_data):

        chunk = corrupted_data[
            offset:offset + FIRMWARE_CHUNK_SIZE
        ]

        packet = build_data_packet(offset, chunk)

        acknowledged = False

        for attempt in range(1, MAX_RETRIES + 1):

            serial_handler.send(packet)

            response = serial_handler.receive_response()

            if response is True:
                acknowledged = True
                break

            elif response is False:
                print(f"\nDATA packet rejected at offset {offset}.")
                return False

            else:
                print(f"ACK timeout. Retry {attempt}/{MAX_RETRIES}")

        if not acknowledged:
            print("\nMaximum retries reached.")
            return False

        offset += len(chunk)

        print(
            f"\rTransferred: {offset}/{len(corrupted_data)} bytes",
            end=""
        )

    print("\nFirmware transfer completed.")

    # Step 3: Request CRC verification
    print("\nRequesting final CRC verification...")

    end_packet = build_end_update_packet()

    serial_handler.send(end_packet)

    response = serial_handler.receive_end_response()

    if response is False:
        print("\nSUCCESS: Bootloader rejected corrupted firmware!")
        print("CRC mismatch detected as expected.")
        return True

    elif response is True:
        print("\nFAILURE: Bootloader accepted corrupted firmware!")
        return False

    else:
        print("\nNo response received for END_UPDATE.")
        return False


def main():

    print("\n====================================")
    print("       CRC CORRUPTION TEST")
    print("====================================")

    if len(sys.argv) != 2:
        print("\nUsage:")
        print("python test_crc_corruption.py <firmware.bin>")
        return

    try:
        firmware = FirmwareParser(sys.argv[1])
        firmware.load_firmware()
        firmware.display_info()

    except (FileNotFoundError, ValueError) as error:
        print("\nFirmware Error:", error)
        return

    serial_handler = SerialHandler()

    print("\nAvailable Serial Ports")
    print("----------------------")

    serial_handler.list_ports()

    if not serial_handler.connect():
        return

    try:
        test_crc_corruption(serial_handler, firmware)

    finally:
        serial_handler.disconnect()


if __name__ == "__main__":
    main()
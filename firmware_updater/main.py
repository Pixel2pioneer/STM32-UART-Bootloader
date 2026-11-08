from firmware_parser import FirmwareParser
from serial_handler import SerialHandler

from protocol import (
    build_start_update_packet,
    build_data_packet,
    build_end_update_packet,
    FIRMWARE_CHUNK_SIZE
)

FIRMWARE_VERSION = 0x01000002  # Restore version 1.0.2

import sys
import time

def transfer_firmware(serial_handler, firmware):

    MAX_RETRIES = 3

    # Step 1: Send START_UPDATE
    print("\nStarting firmware update...")

    start_packet = build_start_update_packet(
    firmware.firmware_data,
    FIRMWARE_VERSION
)

    serial_handler.send(start_packet)

    if not serial_handler.receive_start_response():
        print("Firmware update initialization failed!")
        return False

    print("STM32 accepted firmware update.")

    # Step 2: Transfer firmware chunks
    firmware_data = firmware.firmware_data
    firmware_size = firmware.firmware_size

    offset = 0

    while offset < firmware_size:

        chunk = firmware_data[
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
                print(f"\nBootloader rejected packet at offset {offset}.")
                return False

            else:
                print(
                    f"\nACK timeout at offset {offset}. "
                    f"Retry {attempt}/{MAX_RETRIES}"
                )

        if not acknowledged:
            print(f"\nMaximum retries reached at offset {offset}.")
            return False

        offset += len(chunk)

        print(
            f"\rTransferred: {offset}/{firmware_size} bytes",
            end=""
        )

    print("\nFirmware transfer completed.")

    # Step 3: Send END_UPDATE
    print("Requesting final CRC verification...")

    end_packet = build_end_update_packet()

    end_acknowledged = False

    for attempt in range(1, MAX_RETRIES + 1):

        serial_handler.send(end_packet)

        response = serial_handler.receive_end_response()

        if response is True:
            end_acknowledged = True
            break

        elif response is False:
            print("\nBootloader rejected END_UPDATE.")
            return False

        else:
            print(
                f"\nEND_UPDATE ACK timeout. "
                f"Attempt {attempt}/{MAX_RETRIES}"
            )

    if not end_acknowledged:
        print("\nMaximum END_UPDATE attempts reached.")
        return False

    print("\nFirmware update successful!")

    return True

def main():

    print("\n====================================")
    print("       STM32 UART FIRMWARE UPDATER")
    print("====================================")

    if len(sys.argv) != 2:
        print("\nUsage:")
        print("python main.py <firmware.bin>")
        return

    firmware_path = sys.argv[1]

    # Load and validate firmware

    try:
        firmware = FirmwareParser(firmware_path)

        firmware.load_firmware()

        firmware.display_info()

    except (FileNotFoundError, ValueError) as error:
        print(f"\nFirmware Error: {error}")
        return

    # Detect available serial ports

    print("\nAvailable Serial Ports")
    print("----------------------")

    serial_handler = SerialHandler()
    serial_handler.list_ports()

    # Connect to STM32

    if not serial_handler.connect():
        return

    try:
        transfer_firmware(serial_handler, firmware)

    finally:
        serial_handler.disconnect()


if __name__ == "__main__":
    main()
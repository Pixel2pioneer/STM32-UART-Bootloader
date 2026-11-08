import serial
import time
import struct

from firmware_parser import FirmwareParser
from protocol import (
    build_start_update_packet,
    build_data_packet,
    calculate_crc32,
    FIRMWARE_CHUNK_SIZE
)

PORT = "COM3"
BAUDRATE = 115200

FIRMWARE_VERSION = 0x01000003  # Test version 1.0.3

ACK = b'\x79'
NACK = b'\x1F'


def main():

    firmware = FirmwareParser(
    r"..\uart_application\Debug\uart_application.bin"
)

    firmware.load_firmware()

    firmware_data = firmware.firmware_data

    firmware_size = len(firmware_data)
    firmware_crc = calculate_crc32(firmware_data)

    print("Firmware size:", firmware_size)
    print("Firmware CRC:", hex(firmware_crc))

    ser = serial.Serial(
        PORT,
        BAUDRATE,
        timeout=60
    )

    time.sleep(2)

    # Step 1: Send START_UPDATE
    print("\nSending START_UPDATE...")

    start_packet = build_start_update_packet(
        firmware_data,
        FIRMWARE_VERSION
    )

    ser.write(start_packet)
    ser.flush()

    response = ser.read(1)

    if response != ACK:
        print("START_UPDATE failed:", response)
        ser.close()
        return

    print("START_UPDATE ACK received.")

    # Step 2: Send only the first firmware chunk
    chunk = firmware_data[:FIRMWARE_CHUNK_SIZE]

    data_packet = build_data_packet(0, chunk)

    print("\nSending first DATA_TRANSFER packet...")

    ser.write(data_packet)
    ser.flush()

    response = ser.read(1)

    if response == ACK:
        print("First DATA_TRANSFER ACK received.")
    else:
        print("DATA_TRANSFER failed:", response)
        ser.close()
        return

    # Step 3: Simulate communication interruption
    print("\nSIMULATING INTERRUPTED UPDATE.")
    print("Closing serial connection without END_UPDATE.")

    ser.close()

    print("\nInterruption test initiated.")


if __name__ == "__main__":
    main()
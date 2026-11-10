from serial_handler import SerialHandler
from protocol import (
    build_data_packet,
    build_start_update_packet,
    build_end_update_packet,
    build_packet,
    CMD_DATA_TRANSFER,
    CMD_START_UPDATE,
    CMD_END_UPDATE
)

import time
import struct

PORT = "COM3"
BAUD_RATE = 115200


def test_data_before_update(serial_handler):

    print("\nTEST 1: DATA_TRANSFER before START_UPDATE")

    # Send DATA_TRANSFER without starting a firmware update
    packet = build_data_packet(0, b"\x11\x22\x33\x44")

    serial_handler.send(packet)

    response = serial_handler.receive_response()

    if response is False:
        print("[PASS] Bootloader correctly rejected DATA_TRANSFER.")

    elif response is True:
        print("[FAIL] Bootloader unexpectedly accepted DATA_TRANSFER.")

    else:
        print("[FAIL] No valid response received.")

def test_incorrect_offset(serial_handler):

    print("\nTEST 2: Incorrect firmware offset")

    # Initialize an update with 200 bytes of test firmware
    firmware_data = bytes([0x55] * 200)
    firmware_version = 0x01000002

    start_packet = build_start_update_packet(
        firmware_data,
        firmware_version
    )

    serial_handler.send(start_packet)

    response = serial_handler.receive_start_response()

    if response is not True:
        print("[FAIL] START_UPDATE was not acknowledged.")
        return

    print("[INFO] START_UPDATE acknowledged.")

    # TEST 2: Incorrect offset (128 instead of 0)
    packet = build_data_packet(128, bytes([0xAA] * 128))

    serial_handler.send(packet)

    response = serial_handler.receive_response()

    if response is False:
        print("[PASS] Bootloader rejected incorrect offset.")
    elif response is True:
        print("[FAIL] Bootloader accepted incorrect offset.")
    else:
        print("[FAIL] No valid response received.")

    # TEST 3: Unaligned offset (1)
    print("\nTEST 3: Unaligned firmware offset")

    packet = build_data_packet(1, bytes([0xAA] * 128))

    serial_handler.send(packet)

    response = serial_handler.receive_response()

    if response is False:
        print("[PASS] Bootloader rejected unaligned offset.")
    elif response is True:
        print("[FAIL] Bootloader accepted unaligned offset.")
    else:
        print("[FAIL] No valid response received.")

def test_invalid_payload_length(serial_handler):

    print("\nTEST 4A: Payload length below minimum")

    # DATA_TRANSFER payload containing only 4 bytes
    # Missing firmware data
    packet = build_packet(CMD_DATA_TRANSFER, b"\x00\x00\x00\x00")

    serial_handler.send(packet)

    response = serial_handler.receive_response()

    if response is False:
        print("[PASS] Bootloader rejected payload length 4.")
    else:
        print("[FAIL] Unexpected response:", response)

    print("\nTEST 4B: Payload length above maximum")

    # DATA_TRANSFER payload containing 133 bytes
    payload = bytes([0xAA] * 133)

    packet = build_packet(CMD_DATA_TRANSFER, payload)

    serial_handler.send(packet)

    response = serial_handler.receive_response()

    if response is False:
        print("[PASS] Bootloader rejected payload length 133.")
    else:
        print("[FAIL] Unexpected response:", response)

def test_firmware_boundary(serial_handler):

    print("\nTEST 5: Firmware boundary validation")

    # Send a valid first chunk at offset 0
    packet = build_data_packet(
        0,
        bytes([0x55] * 128)
    )

    serial_handler.send(packet)

    response = serial_handler.receive_response()

    if response is not True:
        print("[FAIL] Initial valid data packet was rejected.")
        return

    print("[INFO] Initial 128-byte chunk accepted.")

    # Attempt another 128 bytes at offset 128.
    # Declared firmware size is 200 bytes in the current test.
    packet = build_data_packet(
        128,
        bytes([0xAA] * 128)
    )

    serial_handler.send(packet)

    response = serial_handler.receive_response()

    if response is False:
        print("[PASS] Bootloader rejected data exceeding firmware size.")
    elif response is True:
        print("[FAIL] Bootloader accepted data exceeding firmware size.")
    else:
        print("[FAIL] No valid response received.")

def test_identical_duplicate(serial_handler):

    print("\nTEST 6A: Identical duplicate packet")

    # Initialize firmware update
    firmware_data = bytes([0x55] * 256)
    firmware_version = 0x01000002

    start_packet = build_start_update_packet(
        firmware_data,
        firmware_version
    )

    serial_handler.send(start_packet)

    response = serial_handler.receive_start_response()

    if response is not True:
        print("[FAIL] START_UPDATE was not acknowledged.")
        return

    print("[INFO] START_UPDATE acknowledged.")

    # Create a valid 128-byte packet
    chunk = bytes([0xAA] * 128)

    packet = build_data_packet(0, chunk)

    # First transmission
    print("[INFO] Sending original packet...")

    serial_handler.send(packet)

    response = serial_handler.receive_response()

    if response is not True:
        print("[FAIL] Original packet was not acknowledged.")
        return

    print("[PASS] Original packet acknowledged.")

    # Second transmission: identical packet
    print("[INFO] Retransmitting identical packet...")

    serial_handler.send(packet)

    response = serial_handler.receive_response()

    if response is True:
        print("[PASS] Identical duplicate packet acknowledged.")
    elif response is False:
        print("[FAIL] Identical duplicate packet rejected.")
    else:
        print("[FAIL] No valid response received.")

def test_modified_duplicate(serial_handler):

    print("\nTEST 6B: Modified duplicate packet")

    # Initialize firmware update
    firmware_data = bytes([0x55] * 256)
    firmware_version = 0x01000002

    start_packet = build_start_update_packet(
        firmware_data,
        firmware_version
    )

    serial_handler.send(start_packet)

    response = serial_handler.receive_start_response()

    if response is not True:
        print("[FAIL] START_UPDATE was not acknowledged.")
        return

    print("[INFO] START_UPDATE acknowledged.")

    # Send original packet
    original_chunk = bytearray([0xAA] * 128)

    packet = build_data_packet(0, original_chunk)

    serial_handler.send(packet)

    response = serial_handler.receive_response()

    if response is not True:
        print("[FAIL] Original packet was not acknowledged.")
        return

    print("[INFO] Original packet acknowledged.")

    # Modify one byte while keeping the same offset
    modified_chunk = bytearray(original_chunk)
    modified_chunk[10] ^= 0x01

    packet = build_data_packet(0, modified_chunk)

    print("[INFO] Sending modified duplicate packet...")

    serial_handler.send(packet)

    response = serial_handler.receive_response()

    if response is False:
        print("[PASS] Bootloader rejected modified duplicate.")
    elif response is True:
        print("[FAIL] Bootloader accepted modified duplicate.")
    else:
        print("[FAIL] No valid response received.")

def test_data_after_completion(serial_handler):

    print("\nTEST 7: DATA_TRANSFER after transfer completion")

    # Initialize an update with 128 bytes of firmware
    firmware_data = bytes([0x55] * 128)
    firmware_version = 0x01000002

    start_packet = build_start_update_packet(
        firmware_data,
        firmware_version
    )

    serial_handler.send(start_packet)

    response = serial_handler.receive_start_response()

    if response is not True:
        print("[FAIL] START_UPDATE was not acknowledged.")
        return

    print("[INFO] START_UPDATE acknowledged.")

    # Send all 128 bytes
    packet = build_data_packet(
        0,
        firmware_data
    )

    serial_handler.send(packet)

    response = serial_handler.receive_response()

    if response is not True:
        print("[FAIL] Firmware data was not acknowledged.")
        return

    print("[INFO] Firmware transfer completed.")

    # Send additional data after completion
    extra_data = bytes([0xAA] * 128)

    packet = build_data_packet(
        128,
        extra_data
    )

    serial_handler.send(packet)

    response = serial_handler.receive_response()

    if response is False:
        print("[PASS] Bootloader rejected DATA_TRANSFER after completion.")
    elif response is True:
        print("[FAIL] Bootloader accepted additional data.")
    else:
        print("[FAIL] No valid response received.")

def test_out_of_sequence_packet(serial_handler):

    print("\nTEST 8: Out-of-sequence DATA_TRANSFER")

    firmware_data = bytes([0x55] * 384)
    firmware_version = 0x01000002

    # Initialize firmware update
    start_packet = build_start_update_packet(
        firmware_data,
        firmware_version
    )

    serial_handler.send(start_packet)

    response = serial_handler.receive_start_response()

    if response is not True:
        print("[FAIL] START_UPDATE was not acknowledged.")
        return

    print("[INFO] START_UPDATE acknowledged.")

    # Send first valid chunk at offset 0
    packet = build_data_packet(
        0,
        bytes([0xAA] * 128)
    )

    serial_handler.send(packet)

    response = serial_handler.receive_response()

    if response is not True:
        print("[FAIL] First data packet was rejected.")
        return

    print("[INFO] First data packet acknowledged.")

    # Skip offset 128 and send at offset 256
    packet = build_data_packet(
        256,
        bytes([0xBB] * 128)
    )

    serial_handler.send(packet)

    response = serial_handler.receive_response()

    if response is False:
        print("[PASS] Bootloader rejected out-of-sequence packet.")
    elif response is True:
        print("[FAIL] Bootloader accepted out-of-sequence packet.")
    else:
        print("[FAIL] No valid response received.")

def test_invalid_firmware_size(serial_handler):

    print("\nTEST 9A: Zero firmware size")

    firmware_version = 0x01000002

    # Construct START_UPDATE with firmware size = 0
    payload = struct.pack(
        "<III",
        0,
        0,
        firmware_version
    )

    packet = build_packet(CMD_START_UPDATE, payload)

    serial_handler.send(packet)

    response = serial_handler.receive_response()

    if response is False:
        print("[PASS] Bootloader rejected zero firmware size.")
    elif response is True:
        print("[FAIL] Bootloader accepted zero firmware size.")
    else:
        print("[FAIL] No valid response received.")

    print("\nTEST 9B: Firmware size exceeding maximum")

    # APP_MAX_SIZE = 0x001E0000
    oversized_firmware_size = 0x001E0001

    payload = struct.pack(
        "<III",
        oversized_firmware_size,
        0,
        firmware_version
    )

    packet = build_packet(CMD_START_UPDATE, payload)

    serial_handler.send(packet)

    response = serial_handler.receive_response()

    if response is False:
        print("[PASS] Bootloader rejected oversized firmware.")
    elif response is True:
        print("[FAIL] Bootloader accepted oversized firmware.")
    else:
        print("[FAIL] No valid response received.")

def test_invalid_firmware_version(serial_handler):

    print("\nTEST 10: Invalid firmware version")

    firmware_size = 256
    firmware_crc = 0
    firmware_version = 0

    payload = struct.pack(
        "<III",
        firmware_size,
        firmware_crc,
        firmware_version
    )

    packet = build_packet(CMD_START_UPDATE, payload)

    serial_handler.send(packet)

    response = serial_handler.receive_response()

    if response is False:
        print("[PASS] Bootloader rejected firmware version 0.")
    elif response is True:
        print("[FAIL] Bootloader accepted invalid firmware version.")
    else:
        print("[FAIL] No valid response received.")

def test_invalid_start_payload_length(serial_handler):

    print("\nTEST 11A: START_UPDATE payload too short")

    # Send START_UPDATE with only 8 bytes
    payload = bytes([0x00] * 8)

    packet = build_packet(CMD_START_UPDATE, payload)

    serial_handler.send(packet)

    response = serial_handler.receive_response()

    if response is False:
        print("[PASS] Bootloader rejected 8-byte payload.")
    elif response is True:
        print("[FAIL] Bootloader accepted invalid payload.")
    else:
        print("[FAIL] No valid response received.")

    print("\nTEST 11B: START_UPDATE payload too long")

    # Send START_UPDATE with 13 bytes
    payload = bytes([0x00] * 13)

    packet = build_packet(CMD_START_UPDATE, payload)

    serial_handler.send(packet)

    response = serial_handler.receive_response()

    if response is False:
        print("[PASS] Bootloader rejected 13-byte payload.")
    elif response is True:
        print("[FAIL] Bootloader accepted invalid payload.")
    else:
        print("[FAIL] No valid response received.")

def test_invalid_end_payload_length(serial_handler):

    print("\nTEST 12A: END_UPDATE with 1-byte payload")

    # Send END_UPDATE with an invalid 1-byte payload
    payload = bytes([0xAA])

    packet = build_packet(CMD_END_UPDATE, payload)

    serial_handler.send(packet)

    response = serial_handler.receive_response()

    if response is False:
        print("[PASS] Bootloader rejected 1-byte END_UPDATE payload.")
    elif response is True:
        print("[FAIL] Bootloader accepted invalid END_UPDATE payload.")
    else:
        print("[FAIL] No valid response received.")

    print("\nTEST 12B: END_UPDATE with 4-byte payload")

    # Send END_UPDATE with an invalid 4-byte payload
    payload = bytes([0xAA] * 4)

    packet = build_packet(CMD_END_UPDATE, payload)

    serial_handler.send(packet)

    response = serial_handler.receive_response()

    if response is False:
        print("[PASS] Bootloader rejected 4-byte END_UPDATE payload.")
    elif response is True:
        print("[FAIL] Bootloader accepted invalid END_UPDATE payload.")
    else:
        print("[FAIL] No valid response received.")

def test_unknown_command(serial_handler):

    print("\nTEST 13: Unknown command ID")

    # Send an unsupported command ID (0x99)
    unknown_command_id = 0x99

    packet = build_packet(unknown_command_id)

    serial_handler.send(packet)

    response = serial_handler.receive_response()

    if response is False:
        print("[PASS] Bootloader rejected unknown command.")
    elif response is True:
        print("[FAIL] Bootloader accepted unknown command.")
    else:
        print("[FAIL] No valid response received.")

def test_duplicate_start_update(serial_handler):

    print("\nTEST 14: Duplicate START_UPDATE")

    firmware_data = bytes([0x55] * 256)
    firmware_version = 0x01000002

    # First START_UPDATE
    start_packet = build_start_update_packet(
        firmware_data,
        firmware_version
    )

    serial_handler.send(start_packet)

    response = serial_handler.receive_start_response()

    if response is not True:
        print("[FAIL] First START_UPDATE was not acknowledged.")
        return

    print("[INFO] First START_UPDATE acknowledged.")

    # Second START_UPDATE without completing the first
    print("[INFO] Sending duplicate START_UPDATE...")

    serial_handler.send(start_packet)

    response = serial_handler.receive_response()

    if response is False:
        print("[PASS] Bootloader rejected duplicate START_UPDATE.")
    elif response is True:
        print("[FAIL] Bootloader accepted duplicate START_UPDATE.")
    else:
        print("[FAIL] No valid response received.")

def test_repeated_end_update(serial_handler):

    print("\nTEST 15: Repeated END_UPDATE")

    firmware_data = bytes([0x55] * 128)
    firmware_version = 0x01000002

    # Initialize firmware update
    start_packet = build_start_update_packet(
        firmware_data,
        firmware_version
    )

    serial_handler.send(start_packet)

    response = serial_handler.receive_start_response()

    if response is not True:
        print("[FAIL] START_UPDATE was not acknowledged.")
        return

    print("[INFO] START_UPDATE acknowledged.")

    # Transfer complete firmware
    packet = build_data_packet(0, firmware_data)

    serial_handler.send(packet)

    response = serial_handler.receive_response()

    if response is not True:
        print("[FAIL] DATA_TRANSFER was not acknowledged.")
        return

    print("[INFO] Firmware data transferred.")

    # First END_UPDATE
    end_packet = build_end_update_packet()

    serial_handler.send(end_packet)

    response = serial_handler.receive_end_response()

    if response is not True:
        print("[FAIL] First END_UPDATE failed.")
        return

    print("[PASS] First END_UPDATE acknowledged.")

    # Repeat END_UPDATE
    print("[INFO] Sending repeated END_UPDATE...")

    serial_handler.send(end_packet)

    response = serial_handler.receive_end_response()

    if response is True:
        print("[PASS] Repeated END_UPDATE acknowledged.")
    elif response is False:
        print("[FAIL] Repeated END_UPDATE rejected.")
    else:
        print("[FAIL] No valid response received.")

def wait_for_board_reset(message, serial_handler):
    print("\n" + "=" * 55)
    print(message)
    print("1. Press the RESET button on the STM32 board.")
    print("2. Wait for the bootloader startup message.")
    input("3. Press ENTER here when ready...")

    # Allow UART startup transmission to finish
    time.sleep(0.5)

    # Clear stale startup messages from UART receive buffer
    serial_handler.connection.reset_input_buffer()

    print("[INFO] UART receive buffer cleared.")
    print("=" * 55)


def main():

    serial_handler = SerialHandler(PORT, BAUD_RATE)

    if not serial_handler.connect():
        return

    try:

        print("\nSTM32 UART BOOTLOADER - INVALID PACKET TEST SUITE")
        print("=" * 55)
        print("Ensure the STM32 board is currently in bootloader mode.")
        input("Press ENTER to begin testing...")
        time.sleep(0.5)
        serial_handler.connection.reset_input_buffer()

        print("[INFO] Initial UART receive buffer cleared.")

        # GROUP 1: TC01 - TC05
        print("\n\n========== GROUP 1: TC01 - TC05 ==========")

        test_data_before_update(serial_handler)
        test_incorrect_offset(serial_handler)
        test_invalid_payload_length(serial_handler)
        test_firmware_boundary(serial_handler)

        # GROUP 2: TC06A
        wait_for_board_reset("Prepare for TC06A", serial_handler)

        print("\n\n========== GROUP 2: TC06A ==========")
        test_identical_duplicate(serial_handler)

        # GROUP 3: TC06B
        wait_for_board_reset("Prepare for TC06B", serial_handler)

        print("\n\n========== GROUP 3: TC06B ==========")
        test_modified_duplicate(serial_handler)

        # GROUP 4: TC07
        wait_for_board_reset("Prepare for TC07", serial_handler)

        print("\n\n========== GROUP 4: TC07 ==========")
        test_data_after_completion(serial_handler)

        # GROUP 5: TC08
        wait_for_board_reset("Prepare for TC08", serial_handler)

        print("\n\n========== GROUP 5: TC08 ==========")
        test_out_of_sequence_packet(serial_handler)

        # GROUP 6: TC09 - TC13
        wait_for_board_reset("Prepare for TC09 - TC13", serial_handler)

        print("\n\n========== GROUP 6: TC09 - TC13 ==========")

        test_invalid_firmware_size(serial_handler)
        test_invalid_firmware_version(serial_handler)
        test_invalid_start_payload_length(serial_handler)
        test_invalid_end_payload_length(serial_handler)
        test_unknown_command(serial_handler)

        # GROUP 7: TC14
        wait_for_board_reset("Prepare for TC14", serial_handler)

        print("\n\n========== GROUP 7: TC14 ==========")
        test_duplicate_start_update(serial_handler)

        # GROUP 8: TC15
        wait_for_board_reset("Prepare for TC15", serial_handler)

        print("\n\n========== GROUP 8: TC15 ==========")
        test_repeated_end_update(serial_handler)

        print("\n\n========== TEST SUITE FINISHED ==========")
        print("Review the PASS/FAIL results above.")
        print("Restore the original application firmware before normal use.")

    finally:
        serial_handler.disconnect()


if __name__ == "__main__":
    main()
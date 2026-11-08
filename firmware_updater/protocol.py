import struct
import zlib

# Bootloader protocol definitions

BOOT_START_BYTE = 0xAA

CMD_GET_VERSION = 0x01
CMD_GET_STATUS = 0x02
CMD_GET_APP_INFO = 0x03
CMD_START_UPDATE = 0x04
CMD_DATA_TRANSFER = 0x05
CMD_END_UPDATE = 0x06

MAX_PAYLOAD_SIZE = 255
FIRMWARE_CHUNK_SIZE = 128


def build_packet(command_id, payload=b""):
    """
    Construct a bootloader packet.

    Format:
    START_BYTE | COMMAND_ID | LENGTH | PAYLOAD
    """

    if len(payload) > MAX_PAYLOAD_SIZE:
        raise ValueError("Payload exceeds maximum size")

    packet = struct.pack(
        "<BBB",
        BOOT_START_BYTE,
        command_id,
        len(payload)
    ) + payload

    return packet


def calculate_crc32(firmware_data):
    """
    Calculate CRC32 of firmware.
    """

    return zlib.crc32(firmware_data) & 0xFFFFFFFF


def build_start_update_packet(firmware_data):
    """
    Construct START_UPDATE packet.

    Payload:
    Firmware Size (4 bytes)
    Expected CRC32 (4 bytes)
    """

    firmware_size = len(firmware_data)
    firmware_crc = calculate_crc32(firmware_data)

    payload = struct.pack(
        "<II",
        firmware_size,
        firmware_crc
    )

    return build_packet(CMD_START_UPDATE, payload)


def build_data_packet(offset, chunk):
    """
    Construct DATA_TRANSFER packet.

    Payload:
    Offset (4 bytes) + Firmware Data
    """

    payload = struct.pack("<I", offset) + chunk

    return build_packet(CMD_DATA_TRANSFER, payload)

def build_end_update_packet():
    """
    Construct END_UPDATE packet.

    Payload: Empty
    """

    return build_packet(CMD_END_UPDATE)
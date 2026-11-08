import os
import zlib

# STM32F439ZI application memory configuration

APP_START_ADDRESS = 0x08020000
APP_END_ADDRESS = 0x08200000

APP_MAX_SIZE = APP_END_ADDRESS - APP_START_ADDRESS


class FirmwareParser:

    def __init__(self, firmware_path):

        self.firmware_path = firmware_path
        self.firmware_data = None
        self.firmware_size = 0
        self.firmware_crc = 0

    def load_firmware(self):

        if not os.path.isfile(self.firmware_path):
            raise FileNotFoundError("Firmware file not found!")

        with open(self.firmware_path, "rb") as firmware:

            self.firmware_data = firmware.read()

        self.firmware_size = len(self.firmware_data)

        if self.firmware_size == 0:
            raise ValueError("Firmware file is empty!")

        if self.firmware_size > APP_MAX_SIZE:
            raise ValueError("Firmware exceeds application Flash capacity!")

        self.firmware_crc = zlib.crc32(self.firmware_data) & 0xFFFFFFFF

        return True

    def display_info(self):

        print("\nFirmware Information")
        print("--------------------")

        print(f"File       : {self.firmware_path}")
        print(f"Size       : {self.firmware_size} bytes")
        print(f"CRC32      : 0x{self.firmware_crc:08X}")
        print(f"Start Addr : 0x{APP_START_ADDRESS:08X}")
        print(f"End Addr   : 0x{APP_END_ADDRESS:08X}")
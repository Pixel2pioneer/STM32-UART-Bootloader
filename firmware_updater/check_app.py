import serial
import time

ser = serial.Serial("COM3", 115200, timeout=2)

# CMD_GET_APP_INFO
packet = bytes([0xAA, 0x03, 0x00])

ser.write(packet)
time.sleep(0.5)

response = ser.read_all()

print("Bootloader response:")
print(response.decode(errors="replace"))

ser.close()
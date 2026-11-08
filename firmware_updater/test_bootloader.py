import serial
import time

PORT = "COM3"
BAUDRATE = 115200

START_BYTE = 0xAA

CMD_GET_VERSION = 0x01
CMD_GET_APP_INFO = 0x03


def send_command(ser, command):

    packet = bytes([
        START_BYTE,
        command,
        0x00
    ])

    ser.reset_input_buffer()
    ser.write(packet)
    ser.flush()

    time.sleep(0.2)

    response = ser.read(ser.in_waiting)

    return response.decode("ascii", errors="replace")


try:

    with serial.Serial(PORT, BAUDRATE, timeout=2) as ser:

        time.sleep(2)

        print("\nTesting GET_VERSION...")
        print(send_command(ser, CMD_GET_VERSION))

        print("\nTesting GET_APP_INFO...")
        print(send_command(ser, CMD_GET_APP_INFO))

except serial.SerialException as error:

    print("Serial communication error:", error)
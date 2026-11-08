import serial
import serial.tools.list_ports


class SerialHandler:

    def __init__(self, port="COM3", baudrate=115200, timeout=2):

        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.connection = None

    def list_ports(self):
        """List available serial ports."""

        ports = serial.tools.list_ports.comports()

        for port in ports:
            print(f"{port.device} - {port.description}")

    def connect(self):
        """Establish UART connection."""

        try:
            self.connection = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=self.timeout
            )

            print(f"Connected to {self.port}")
            return True

        except serial.SerialException as error:

            print(f"Connection failed: {error}")
            return False

    def send(self, data):
        """Transmit bytes through UART."""

        if self.connection and self.connection.is_open:
            self.connection.write(data)
            self.connection.flush()

    def receive(self, size=1):
        """Receive bytes through UART."""

        if self.connection and self.connection.is_open:
            return self.connection.read(size)

        return b""

    def receive_response(self):
        """Receive and validate ACK/NACK response."""

        response = self.receive(1)

        if response == b'\x79':
            return True

        elif response == b'\x1F':
            print("Bootloader returned NACK.")
            return False

        else:
            print("Invalid response or timeout:", response)
            return False

    def receive_start_response(self):
        """Receive STM32 diagnostic message and ACK/NACK."""

        old_timeout = self.connection.timeout
        self.connection.timeout = 60

        try:
            response_data = bytearray()

            while True:
                received = self.connection.read(1)

                if not received:
                    print("\nTimed out waiting for STM32 response.")
                    print("Received data:", response_data)
                    return False

                if received == b'\x79':
                    print("\nSTM32 returned ACK.")
                    if response_data:
                        print(response_data.decode(errors="replace").strip())
                    return True

                elif received == b'\x1F':
                    print("\nSTM32 returned NACK.")
                    if response_data:
                        print(response_data.decode(errors="replace").strip())
                    return False

                else:
                    response_data.extend(received)

        finally:
            self.connection.timeout = old_timeout

    def disconnect(self):
        """Close UART connection."""

        if self.connection and self.connection.is_open:
            self.connection.close()
            print("Serial connection closed.")
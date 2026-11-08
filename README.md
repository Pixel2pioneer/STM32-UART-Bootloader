# STM32 UART Bootloader & Firmware Updater

A custom UART-based bootloader implementation for the **STM32F439ZI** microcontroller, featuring firmware reception, Flash programming, CRC32 integrity verification, application metadata management, application validation, and automatic application booting.

The project includes a Python-based firmware updater that communicates with the STM32 bootloader over UART to perform firmware updates, with reliability mechanisms for packet handling and firmware recovery.

## Project Structure

```text
STM32-UART-Bootloader/
│
├── uartbootloader/
│   ├── Core/
│   ├── Drivers/
│   └── ...
│
├── uart_application/
│   ├── Core/
│   ├── Drivers/
│   └── ...
│
├── firmware_updater/
│   ├── main.py
│   ├── protocol.py
│   ├── serial_handler.py
│   ├── firmware_parser.py
│   ├── check_app.py
│   └── requirements.txt
│
├── images/
│   ├── firmware_update_success.jpeg
│   ├── application_running.jpeg
│   └── bootloader_uart.png
│
├── .gitignore
└── README.md
```

## Hardware & Development Environment

| Component | Specification |
|---|---|
| Microcontroller | STM32F439ZI |
| Development Board | NUCLEO-F439ZI |
| Architecture | ARM Cortex-M4 |
| IDE | STM32CubeIDE |
| Firmware Language | Embedded C |
| Host-side Updater | Python |
| Communication Interface | USART3 |
| UART TX | PD8 |
| UART RX | PD9 |
| Baud Rate | 115200 |
| Serial Interface | ST-LINK Virtual COM Port |

## Flash Memory Layout

The STM32 internal Flash memory is partitioned into three regions.

| Region | Start Address | Size | Sectors |
|---|---|---|---|
| Bootloader | 0x08000000 | 64 KB | 0–3 |
| Metadata | 0x08010000 | 64 KB | 4 |
| Application | 0x08020000 | 1920 KB | 5–23 |

The bootloader and metadata regions are preserved during application firmware updates. Only the application Flash sectors are erased and programmed during an update.

## Implemented Features

### 1. Bootloader Architecture

- Separate bootloader and application projects.
- Independent linker scripts.
- Dedicated Flash memory partitioning.
- Application vector table relocation.
- Bootloader entry using the onboard B1 USER button.
- Automatic application boot when a valid application is available.
- Protected bootloader Flash region during firmware updates.

### 2. Application Validation & Handover

- Initial Stack Pointer validation against SRAM boundaries.
- Reset Handler address validation.
- Application Flash address range verification.
- Application metadata validation.
- CRC32 verification before application execution.
- Interrupt and SysTick cleanup before application handover.
- Assembly-based application jump.
- Vector Table Offset Register (VTOR) relocation.

### 3. UART Firmware Update Protocol

Communication between the Python updater and STM32 bootloader uses a custom packet-based UART protocol.

**Packet Format:**

```text
[START_BYTE] [COMMAND_ID] [PAYLOAD_LENGTH] [PAYLOAD]
```

| Parameter | Value |
|---|---|
| Start Byte | 0xAA |
| ACK | 0x79 |
| NACK | 0x1F |
| Maximum Payload | 255 bytes |
| Firmware Chunk Size | 128 bytes |

**Supported Commands:**

| Command | Command ID | Description |
|---|---|---|
| GET_VERSION | 0x01 | Retrieve bootloader version |
| GET_STATUS | 0x02 | Retrieve bootloader status |
| GET_APP_INFO | 0x03 | Retrieve application information and validity |
| START_UPDATE | 0x04 | Initiate firmware update |
| DATA_TRANSFER | 0x05 | Transfer firmware data |
| END_UPDATE | 0x06 | Complete firmware update and verify CRC |

### 4. Flash Programming & Metadata Management

- Application Flash sector erasure.
- Firmware programming using STM32 HAL Flash APIs.
- Sequential firmware chunk reception.
- Firmware offset and boundary validation.
- Application metadata storage in a dedicated Flash sector.
- Metadata invalidation before firmware updates.
- Valid marker programmed only after successful CRC verification.
- Protection of bootloader and metadata regions during application erasure.

### 5. Firmware Integrity Verification

- CRC32 calculation on the Python side.
- CRC32 calculation on the STM32 side.
- Comparison of received and calculated firmware CRC.
- Application validation using stored metadata.
- Verification of firmware size and application memory boundaries.

### 6. Python Firmware Updater

- Firmware binary file loading.
- Firmware size validation.
- CRC32 calculation.
- Serial port detection.
- UART communication using PySerial.
- Packet construction and transmission.
- ACK/NACK response handling.
- Firmware transfer progress monitoring.
- Final firmware verification.

### 7. Firmware Transfer Reliability

- Duplicate DATA packet detection using packet offset, length, and Flash data comparison.
- Re-acknowledgement of previously accepted identical DATA packets.
- Prevention of repeated Flash programming for duplicate packets.
- Validation of packet offsets and payload boundaries.
- Tracking of the last successfully accepted firmware packet.
- Handling of repeated END_UPDATE requests after successful completion.

### 8. Interrupted Firmware Update Recovery

- Application metadata invalidation before starting a firmware update.
- Prevention of incomplete firmware from being treated as a valid application.
- Bootloader remains operational when application validation fails.
- Support for initiating a fresh firmware update after an interrupted update.
- Recovery of application execution through successful firmware reprogramming and metadata validation.

## Firmware Update Workflow

```text
       Python Firmware Updater
                |
                v
          Load Firmware BIN
                |
                v
          Calculate CRC32
                |
                v
          Connect via UART
                |
                v
           START_UPDATE
                |
                v
        Validate Firmware Size
                |
                v
        Invalidate Metadata
                |
                v
        Erase Application Flash
                |
                v
          DATA_TRANSFER
                |
                v
       Validate Packet Offset
                |
                v
       Check Duplicate Packet
                |
                v
       Program Application Flash
                |
                v
          Send ACK / NACK
                |
                v
           END_UPDATE
                |
                v
          Verify CRC32
                |
                v
          Write Metadata
                |
                v
        Validate Application
                |
                v
       Boot Application Firmware
```

## Verified Hardware Test

Successfully performed a complete firmware update using the Python updater and STM32F439ZI Nucleo board.

### Test Configuration

| Parameter | Result |
|---|---|
| Firmware File | uart_application.bin |
| Firmware Size | 6,112 bytes |
| CRC32 | 0xF6213C40 |
| UART Port | COM3 |
| Baud Rate | 115200 |
| Transfer Chunk Size | 128 bytes |
| Flash Erase | Successful |
| Firmware Transfer | Successful |
| CRC Verification | Successful |
| Metadata Programming | Successful |
| Automatic Application Boot | Successful |

### Hardware Demonstration

**1. Successful Firmware Update**

The Python firmware updater successfully transmitted the application binary to the STM32 bootloader.

![Firmware Update Successful](images/firmware_update_success.jpeg)

**2. Application Running on NUCLEO-F439ZI**

After firmware programming and verification, the STM32 successfully booted the application. LD1 was observed blinking at approximately one-second intervals.

![Application Running](images/application_running.jpeg)

**3. Bootloader UART Communication**

UART communication was verified through the ST-LINK Virtual COM Port using PuTTY.

![Bootloader UART Communication](images/bootloader_uart.png)

### Application Recovery Verification

During development, the application metadata and application Flash regions were found erased.

The bootloader remained operational and continued responding to UART commands.

A fresh firmware update was subsequently performed successfully.

The following recovery operations were verified:

- Bootloader UART communication.
- Firmware transfer through the Python updater.
- CRC32 verification.
- Metadata programming.
- Application validation.
- Successful application execution after reset.

The bootloader reported:

```text
Application Address: 0x08020000
Application Status: VALID
```

## Software Requirements

### STM32 Development

- STM32CubeIDE
- STM32 HAL Libraries

### Python Firmware Updater

- Python 3
- PySerial

Install the Python dependencies:

```bash
pip install -r requirements.txt
```

Run the firmware updater from the `firmware_updater` directory:

```bash
python main.py ..\uart_application\Debug\uart_application.bin
```

**Note:** Ensure the STM32 is in bootloader mode and the correct serial port is configured before initiating an update. Close PuTTY or other serial terminal applications before running the updater.

## Project Status

### Phase 1 – Bootloader Architecture: COMPLETED

- Flash memory partitioning.
- Application vector table relocation.
- Application validation.
- Bootloader-to-application handover.
- Manual bootloader entry.
- Automatic application boot.
- Hardware verification.

### Phase 2 – UART Firmware Update: IMPLEMENTED & HARDWARE TESTED

- UART communication protocol.
- Firmware reception.
- Flash erase and programming.
- Metadata management.
- CRC32 firmware integrity verification.
- Python-based firmware updater.
- Automatic application boot after successful update.

### Phase 3 – Reliability & Recovery: IN PROGRESS

- Duplicate DATA packet detection.
- Duplicate packet acknowledgement without repeated Flash programming.
- Firmware offset and packet boundary validation.
- Repeated END_UPDATE request handling.
- Interrupted firmware update recovery mechanism.
- ACK timeout and retransmission improvements.
- Firmware corruption and communication fault-injection testing.

### Future Improvements

- Firmware version management.
- Firmware compatibility checks.
- Comprehensive packet loss and retransmission testing.
- Invalid packet and offset testing.
- Improved UART synchronization and timeout handling.
- Communication stress testing.
- Firmware authenticity and secure update mechanisms.

## Author

**Amrutha Pradeep**

Electronics and Communication Engineering  
Sardar Vallabhbhai National Institute of Technology (SVNIT), Surat
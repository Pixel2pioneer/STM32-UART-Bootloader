# STM32 UART Bootloader & Firmware Updater

A custom UART-based bootloader implementation for the **STM32F439ZI** microcontroller, featuring firmware reception, Flash programming, CRC32 integrity verification, application metadata management, and automatic application booting.

The project includes a Python-based firmware updater that communicates with the STM32 bootloader over UART to perform firmware updates.

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

The bootloader and metadata regions are preserved during application firmware updates.

## Implemented Features

### 1. Bootloader Architecture
- Separate bootloader and application projects.
- Independent linker scripts.
- Dedicated Flash memory partitioning.
- Application vector table relocation.
- Bootloader entry using the onboard B1 USER button.
- Automatic application boot when a valid application is available.

### 2. Application Validation & Handover
- Initial Stack Pointer validation.
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
| GET_APP_INFO | 0x03 | Retrieve application information |
| START_UPDATE | 0x04 | Initiate firmware update |
| DATA_TRANSFER | 0x05 | Transfer firmware data |
| END_UPDATE | 0x06 | Complete firmware update and verify CRC |

### 4. Flash Programming & Metadata Management
- Application Flash sector erasure.
- Firmware programming using STM32 HAL Flash APIs.
- Sequential firmware chunk reception.
- Firmware offset validation.
- Application metadata storage.
- Metadata invalidation before firmware updates.
- Valid marker programmed only after successful CRC verification.

### 5. Firmware Integrity Verification
- CRC32 calculation on the Python side.
- CRC32 calculation on the STM32 side.
- Comparison of received and calculated firmware CRC.
- Application validation using stored metadata.

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
       Invalidate Metadata
                 |
                 v
       Erase Application Flash
                 |
                 v
          DATA_TRANSFER
                 |
                 v
       Program Application Flash
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

#### 1. Successful Firmware Update

The Python firmware updater successfully transmitted the application binary to the STM32 bootloader.

![Firmware Update Successful](images/firmware_update_success.jpeg)

#### 2. Application Running on NUCLEO-F439ZI

After firmware programming and verification, the STM32 automatically booted the application. LD1 was observed blinking at approximately one-second intervals.

![Application Running](images/application_running.jpeg)

#### 3. Bootloader UART Communication

UART communication was verified through the ST-LINK Virtual COM Port using PuTTY.

![Bootloader UART Communication](images/bootloader_uart.png)

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

**Note:** Ensure the STM32 is in bootloader mode and the correct serial port is configured before initiating an update.

## Project Status

### Phase 1 – Bootloader Architecture: COMPLETED
- Flash memory partitioning.
- Application vector table relocation.
- Application validation.
- Bootloader-to-application handover.
- Hardware verification.

### Phase 2 – UART Firmware Update: IMPLEMENTED & HARDWARE TESTED
- UART communication protocol.
- Firmware reception.
- Flash erase and programming.
- Metadata management.
- CRC32 firmware integrity verification.
- Python-based firmware updater.
- Automatic application boot after successful update.

### Future Improvements
- Firmware transfer timeout and recovery mechanisms.
- Duplicate packet detection and retransmission support.
- Interrupted update recovery testing.
- Firmware version management.
- More robust update failure handling.

## Author

**Amrutha Pradeep**

Electronics and Communication Engineering  
Sardar Vallabhbhai National Institute of Technology (SVNIT), Surat
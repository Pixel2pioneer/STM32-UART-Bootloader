# STM32 UART Bootloader

A custom UART bootloader implementation for the STM32F439ZI microcontroller.

## Project Structure

- `uartbootloader/` - Bootloader firmware.
- `uart_application/` - User application firmware.

## Hardware

- Microcontroller: STM32F439ZI
- Architecture: ARM Cortex-M4
- Development Environment: STM32CubeIDE

## Flash Memory Layout

| Region      | Start Address | Size     |
|-------------|---------------|----------|
| Bootloader  | 0x08000000    | 64 KB    |
| Metadata    | 0x08010000    | 64 KB    |
| Application | 0x08020000    | 1920 KB  |

## Implemented Features

- Separate bootloader and application projects.
- Independent linker scripts.
- Application vector table relocation.
- Application vector table validation.
- Initial stack pointer and Reset_Handler validation.
- Interrupt cleanup before application handover.
- Assembly-based application jump.
- Verified bootloader-to-application execution.

## Future Work

- UART-based firmware reception.
- Flash erase and programming.
- Firmware metadata management.
- CRC32 firmware integrity verification.
- Python-based firmware upload utility.
- Firmware update failure handling.

## Project Status

**Phase 1 – Completed**
- Flash memory partitioning.
- Application vector table relocation.
- Application validation.
- Bootloader-to-application handover tested on hardware.

**Phase 2 – In Progress**
- UART firmware reception.
- Flash erase and programming.
- Metadata management.
- CRC32 firmware validation.
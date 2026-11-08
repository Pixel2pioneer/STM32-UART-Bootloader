/* USER CODE BEGIN Header */
/**
  ******************************************************************************
  * @file           : main.c
  * @brief          : Main program body
  ******************************************************************************
  * @attention
  *
  * Copyright (c) 2026 STMicroelectronics.
  * All rights reserved.
  *
  * This software is licensed under terms that can be found in the LICENSE file
  * in the root directory of this software component.
  * If no LICENSE file comes with this software, it is provided AS-IS.
  *
  ******************************************************************************
  */
/* USER CODE END Header */
/* Includes ------------------------------------------------------------------*/
#include "main.h"

/* Private includes ----------------------------------------------------------*/
/* USER CODE BEGIN Includes */
#include <stdio.h>
#include <string.h>
#define APP_ADDRESS  0x08020000U

#define SRAM_START   0x20000000U
#define SRAM_END     0x20030000U
#define APP_END_ADDRESS  0x08200000U
#define APP_MAX_SIZE     (APP_END_ADDRESS - APP_ADDRESS)
/* USER CODE END Includes */

/* Private typedef -----------------------------------------------------------*/
/* USER CODE BEGIN PTD */
typedef void (*pFunction)(void);

typedef struct
{
    uint32_t magicNumber;
    uint32_t firmwareSize;
    uint32_t firmwareCRC;
    uint32_t validMarker;

} ApplicationMetadata;

uint8_t IsMetadataValid(void);
/* USER CODE END PTD */

/* Private define ------------------------------------------------------------*/
/* USER CODE BEGIN PD */
#define BOOT_START_BYTE    0xAA

/* Command IDs */

#define CMD_GET_VERSION    0x01
#define CMD_GET_STATUS     0x02
#define CMD_GET_APP_INFO   0x03
#define CMD_START_UPDATE   0x04
#define CMD_DATA_TRANSFER  0x05
#define CMD_END_UPDATE     0x06

/* Response codes */

#define ACK                0x79
#define NACK               0x1F

/* Packet configuration */

#define MAX_PAYLOAD_SIZE   255
#define FIRMWARE_CHUNK_SIZE 128

#define METADATA_ADDRESS  0x08010000U

#define METADATA_MAGIC    0x424F4F54U

#define APP_VALID_MARKER  0x56414C49U
/* USER CODE END PD */

/* Private macro -------------------------------------------------------------*/
/* USER CODE BEGIN PM */
uint8_t IsApplicationValid(void)
{
	if (!IsMetadataValid())
	  return 0;

    uint32_t app_sp = *(volatile uint32_t*)APP_ADDRESS;
    uint32_t app_reset = *(volatile uint32_t*)(APP_ADDRESS + 4U);

    // Check Stack Pointer range and alignment
    if ((app_sp < SRAM_START) ||
        (app_sp > SRAM_END) ||
        ((app_sp & 0x7U) != 0U))
    {
        return 0;
    }

    // Check Thumb bit
    if ((app_reset & 0x1U) == 0U)
    {
        return 0;
    }

    // Check Reset Handler address
    uint32_t reset_address = app_reset & ~0x1U;

    if ((reset_address < APP_ADDRESS) ||
        (reset_address >= 0x08200000U))
    {
        return 0;
    }

    return 1;
}
/* USER CODE END PM */

/* Private variables ---------------------------------------------------------*/
UART_HandleTypeDef huart3;

/* USER CODE BEGIN PV */
uint8_t rxBuffer[MAX_PAYLOAD_SIZE];

uint8_t startByte;
uint8_t commandID;
uint8_t payloadLength;

uint32_t expectedFirmwareSize;
uint32_t expectedFirmwareCRC;
uint32_t receivedFirmwareBytes;
uint8_t updateInProgress;

uint32_t receivedOffset;
uint16_t receivedChunkSize;
uint32_t nextExpectedOffset;

uint8_t firmwareTransferComplete;

uint32_t lastAcceptedOffset = 0U;
uint32_t lastAcceptedLength = 0U;
uint8_t lastPacketValid = 0U;
/* USER CODE END PV */

/* Private function prototypes -----------------------------------------------*/
void SystemClock_Config(void);
static void MX_GPIO_Init(void);
static void MX_USART3_UART_Init(void);
/* USER CODE BEGIN PFP */
void JumpToApplication(void);
void Bootloader_Cleanup(void);
uint8_t ReceivePacket(void);
HAL_StatusTypeDef EraseApplicationFlash(uint32_t *failedSector);

HAL_StatusTypeDef ProgramApplicationFlash(uint32_t offset,
                                          uint8_t *data,
                                          uint16_t length);
uint8_t IsDuplicatePacket(uint32_t offset,
                          uint8_t *data,
                          uint16_t length);

void SendBootloaderResponse(uint8_t response);

uint32_t CalculateCRC32(uint32_t address, uint32_t length);

HAL_StatusTypeDef WriteApplicationMetadata(uint32_t firmwareSize,
                                           uint32_t firmwareCRC);

HAL_StatusTypeDef InvalidateApplicationMetadata(void);

void Bootloader_CheckAndBootApplication(void);

uint8_t IsBootloaderButtonPressed(void);

/* USER CODE END PFP */

/* Private user code ---------------------------------------------------------*/
/* USER CODE BEGIN 0 */

/* USER CODE END 0 */

/**
  * @brief  The application entry point.
  * @retval int
  */
int main(void)
{

  /* USER CODE BEGIN 1 */

  /* USER CODE END 1 */

  /* MCU Configuration--------------------------------------------------------*/

  /* Reset of all peripherals, Initializes the Flash interface and the Systick. */
  HAL_Init();

  /* USER CODE BEGIN Init */

  /* USER CODE END Init */

  /* Configure the system clock */
  SystemClock_Config();

  /* USER CODE BEGIN SysInit */

  /* USER CODE END SysInit */

  /* Initialize all configured peripherals */
  MX_GPIO_Init();
  MX_USART3_UART_Init();
  /* USER CODE BEGIN 2 */

  uint8_t message[] = "Bootloader UART is working!\r\n";

  HAL_UART_Transmit(&huart3,
                    message,
                    sizeof(message) - 1,
                    HAL_MAX_DELAY);

  if (IsBootloaderButtonPressed())
  {
      uint8_t msg[] = "USER Button: PRESSED\r\n";

      HAL_UART_Transmit(&huart3, msg,
                        sizeof(msg) - 1, HAL_MAX_DELAY);
  }
  else
  {
      uint8_t msg[] = "USER Button: RELEASED\r\n";

      HAL_UART_Transmit(&huart3, msg,
                        sizeof(msg) - 1, HAL_MAX_DELAY);
  }

  Bootloader_CheckAndBootApplication();

  /* USER CODE END 2 */

  /* Infinite loop */
  /* USER CODE BEGIN WHILE */
  while (1)
  {
    /* USER CODE END WHILE */

    /* USER CODE BEGIN 3 */
	  if (ReceivePacket())
	        {
	            if (commandID == CMD_GET_VERSION)
	            {

	                uint8_t version[] = "Bootloader v1.0\r\n";

	                HAL_UART_Transmit(&huart3,
	                                  version,
	                                  sizeof(version) - 1,
	                                  HAL_MAX_DELAY);
	            }
	            else if (commandID == CMD_GET_STATUS)
	            {
	                uint8_t status[] = "Bootloader Status: READY\r\n";

	                HAL_UART_Transmit(&huart3,
	                                  status,
	                                  sizeof(status) - 1,
	                                  HAL_MAX_DELAY);
	            }
	            else if (commandID == CMD_GET_APP_INFO)
	            {
	                uint8_t appAddress[] = "Application Address: 0x08020000\r\n";

	                HAL_UART_Transmit(&huart3,
	                                  appAddress,
	                                  sizeof(appAddress) - 1,
	                                  HAL_MAX_DELAY);

	                if (IsApplicationValid())
	                {
	                    uint8_t valid[] = "Application Status: VALID\r\n";

	                    HAL_UART_Transmit(&huart3,
	                                      valid,
	                                      sizeof(valid) - 1,
	                                      HAL_MAX_DELAY);
	                }
	                else
	                {
	                    uint8_t invalid[] = "Application Status: INVALID\r\n";

	                    HAL_UART_Transmit(&huart3,
	                                      invalid,
	                                      sizeof(invalid) - 1,
	                                      HAL_MAX_DELAY);
	                }
	            }
	            else if (commandID == CMD_START_UPDATE)
	            {
	                if (updateInProgress != 0)
	                {
	                    SendBootloaderResponse(NACK);
	                }
	                else if (payloadLength != 8)
	                {
	                    SendBootloaderResponse(NACK);
	                }
	                else
	                {
	                    expectedFirmwareSize =
	                        (uint32_t)rxBuffer[0] |
	                        ((uint32_t)rxBuffer[1] << 8) |
	                        ((uint32_t)rxBuffer[2] << 16) |
	                        ((uint32_t)rxBuffer[3] << 24);

	                    expectedFirmwareCRC =
	                        (uint32_t)rxBuffer[4] |
	                        ((uint32_t)rxBuffer[5] << 8) |
	                        ((uint32_t)rxBuffer[6] << 16) |
	                        ((uint32_t)rxBuffer[7] << 24);

	                    if ((expectedFirmwareSize == 0U) ||
	                        (expectedFirmwareSize > APP_MAX_SIZE))
	                    {
	                        updateInProgress = 0;

	                        SendBootloaderResponse(NACK);
	                    }
	                    else
	                    {
	                    	HAL_StatusTypeDef metadataStatus =
	                    	    InvalidateApplicationMetadata();

	                    	if (metadataStatus == HAL_OK)
	                    	{
	                    	    uint32_t failedSector = 0xFFFFFFFFU;

	                    	    HAL_StatusTypeDef eraseStatus =
	                    	        EraseApplicationFlash(&failedSector);


	                    	    if (eraseStatus == HAL_OK)
	                    	    {
	                    	        receivedFirmwareBytes = 0;
	                    	        nextExpectedOffset = 0;

	                    	        lastAcceptedOffset = 0U;
	                    	        lastAcceptedLength = 0U;
	                    	        lastPacketValid = 0U;

	                    	        firmwareTransferComplete = 0;
	                    	        updateInProgress = 1;

	                    	        SendBootloaderResponse(ACK);
	                    	    }
	                    	    else
	                    	    {
	                    	        updateInProgress = 0;
	                    	        firmwareTransferComplete = 0;
	                    	        receivedFirmwareBytes = 0;
	                    	        nextExpectedOffset = 0;

	                    	        SendBootloaderResponse(NACK);
	                    	    }
	                    	}
	                    	else
	                    	{
	                    	    SendBootloaderResponse(NACK);
	                    	}
	                    }
	                }
	            }
	            else if (commandID == CMD_DATA_TRANSFER)
	            {
	                if (updateInProgress == 0)
	                {
	                    SendBootloaderResponse(NACK);
	                }
	                else if ((payloadLength < 5) || (payloadLength > 132))
	                {
	                    SendBootloaderResponse(NACK);
	                }
	                else
	                {
	                    receivedOffset =
	                        (uint32_t)rxBuffer[0] |
	                        ((uint32_t)rxBuffer[1] << 8) |
	                        ((uint32_t)rxBuffer[2] << 16) |
	                        ((uint32_t)rxBuffer[3] << 24);

	                    receivedChunkSize = payloadLength - 4U;

	                    /* Check whether this packet is a duplicate */
	                    if (IsDuplicatePacket(receivedOffset,
	                                          &rxBuffer[4],
	                                          receivedChunkSize))
	                    {
	                        SendBootloaderResponse(ACK);
	                    }
	                    else if (firmwareTransferComplete != 0)
	                    {
	                        SendBootloaderResponse(NACK);
	                    }
	                    else
	                    {
	                        /* Validate firmware offset */
	                        if ((receivedOffset != nextExpectedOffset) ||
	                            ((receivedOffset & 0x03U) != 0U))
	                        {
	                            SendBootloaderResponse(NACK);
	                        }
	                        else if ((receivedChunkSize > expectedFirmwareSize) ||
	                                 (receivedOffset > expectedFirmwareSize - receivedChunkSize))
	                        {
	                            SendBootloaderResponse(NACK);
	                        }
	                        else if (((receivedOffset + receivedChunkSize) < expectedFirmwareSize) &&
	                                 ((receivedChunkSize & 0x03U) != 0U))
	                        {
	                            SendBootloaderResponse(NACK);
	                        }
	                        else
	                        {
	                            HAL_StatusTypeDef flashStatus =
	                                ProgramApplicationFlash(receivedOffset,
	                                                        &rxBuffer[4],
	                                                        receivedChunkSize);

	                            if (flashStatus != HAL_OK)
	                            {
	                                SendBootloaderResponse(NACK);
	                            }
	                            else
	                            {
	                                receivedFirmwareBytes += receivedChunkSize;

	                                nextExpectedOffset =
	                                    receivedOffset + receivedChunkSize;

	                                /* Store information about the accepted packet */
	                                lastAcceptedOffset = receivedOffset;
	                                lastAcceptedLength = receivedChunkSize;
	                                lastPacketValid = 1U;

	                                if (receivedFirmwareBytes == expectedFirmwareSize)
	                                {
	                                    firmwareTransferComplete = 1U;
	                                }

	                                SendBootloaderResponse(ACK);
	                            }
	                        }
	                    }
	                }
	            }
	            else if (commandID == CMD_END_UPDATE)
	            {
	                if (payloadLength != 0U)
	                {
	                    SendBootloaderResponse(NACK);
	                }
	                else if (updateInProgress == 0U)
	                {
	                    /*
	                     * Check whether this is a repeated END_UPDATE request.
	                     * The previous update must have completed successfully.
	                     */
	                    if ((firmwareTransferComplete != 0U) &&
	                        (IsMetadataValid() != 0U) &&
	                        (CalculateCRC32(APP_ADDRESS, expectedFirmwareSize) ==
	                         expectedFirmwareCRC))
	                    {
	                        SendBootloaderResponse(ACK);
	                    }
	                    else
	                    {
	                        SendBootloaderResponse(NACK);
	                    }
	                }
	                else if (firmwareTransferComplete == 0U)
	                {
	                    SendBootloaderResponse(NACK);
	                }
	                else
	                {
	                    uint32_t calculatedCRC =
	                        CalculateCRC32(APP_ADDRESS, expectedFirmwareSize);

	                    if (calculatedCRC == expectedFirmwareCRC)
	                    {
	                        HAL_StatusTypeDef metadataStatus =
	                            WriteApplicationMetadata(expectedFirmwareSize,
	                                                     expectedFirmwareCRC);

	                        if (metadataStatus == HAL_OK)
	                        {
	                            updateInProgress = 0U;
	                            SendBootloaderResponse(ACK);
	                        }
	                        else
	                        {
	                            SendBootloaderResponse(NACK);
	                        }
	                    }
	                    else
	                    {
	                        SendBootloaderResponse(NACK);
	                    }
	                }
	            }

	            }
  }
  /* USER CODE END 3 */
}

/**
  * @brief System Clock Configuration
  * @retval None
  */
void SystemClock_Config(void)
{
  RCC_OscInitTypeDef RCC_OscInitStruct = {0};
  RCC_ClkInitTypeDef RCC_ClkInitStruct = {0};

  /** Configure the main internal regulator output voltage
  */
  __HAL_RCC_PWR_CLK_ENABLE();
  __HAL_PWR_VOLTAGESCALING_CONFIG(PWR_REGULATOR_VOLTAGE_SCALE3);

  /** Initializes the RCC Oscillators according to the specified parameters
  * in the RCC_OscInitTypeDef structure.
  */
  RCC_OscInitStruct.OscillatorType = RCC_OSCILLATORTYPE_HSI;
  RCC_OscInitStruct.HSIState = RCC_HSI_ON;
  RCC_OscInitStruct.HSICalibrationValue = RCC_HSICALIBRATION_DEFAULT;
  RCC_OscInitStruct.PLL.PLLState = RCC_PLL_NONE;
  if (HAL_RCC_OscConfig(&RCC_OscInitStruct) != HAL_OK)
  {
    Error_Handler();
  }

  /** Initializes the CPU, AHB and APB buses clocks
  */
  RCC_ClkInitStruct.ClockType = RCC_CLOCKTYPE_HCLK|RCC_CLOCKTYPE_SYSCLK
                              |RCC_CLOCKTYPE_PCLK1|RCC_CLOCKTYPE_PCLK2;
  RCC_ClkInitStruct.SYSCLKSource = RCC_SYSCLKSOURCE_HSI;
  RCC_ClkInitStruct.AHBCLKDivider = RCC_SYSCLK_DIV1;
  RCC_ClkInitStruct.APB1CLKDivider = RCC_HCLK_DIV2;
  RCC_ClkInitStruct.APB2CLKDivider = RCC_HCLK_DIV1;

  if (HAL_RCC_ClockConfig(&RCC_ClkInitStruct, FLASH_LATENCY_0) != HAL_OK)
  {
    Error_Handler();
  }
}

/**
  * @brief USART3 Initialization Function
  * @param None
  * @retval None
  */
static void MX_USART3_UART_Init(void)
{

  /* USER CODE BEGIN USART3_Init 0 */

  /* USER CODE END USART3_Init 0 */

  /* USER CODE BEGIN USART3_Init 1 */

  /* USER CODE END USART3_Init 1 */
  huart3.Instance = USART3;
  huart3.Init.BaudRate = 115200;
  huart3.Init.WordLength = UART_WORDLENGTH_8B;
  huart3.Init.StopBits = UART_STOPBITS_1;
  huart3.Init.Parity = UART_PARITY_NONE;
  huart3.Init.Mode = UART_MODE_TX_RX;
  huart3.Init.HwFlowCtl = UART_HWCONTROL_NONE;
  huart3.Init.OverSampling = UART_OVERSAMPLING_16;
  if (HAL_UART_Init(&huart3) != HAL_OK)
  {
    Error_Handler();
  }
  /* USER CODE BEGIN USART3_Init 2 */

  /* USER CODE END USART3_Init 2 */

}

/**
  * @brief GPIO Initialization Function
  * @param None
  * @retval None
  */
static void MX_GPIO_Init(void)
{
  GPIO_InitTypeDef GPIO_InitStruct = {0};
  /* USER CODE BEGIN MX_GPIO_Init_1 */

  /* USER CODE END MX_GPIO_Init_1 */

  /* GPIO Ports Clock Enable */
  __HAL_RCC_GPIOC_CLK_ENABLE();
  __HAL_RCC_GPIOD_CLK_ENABLE();
  __HAL_RCC_GPIOA_CLK_ENABLE();

  /*Configure GPIO pin : PC13 */
  GPIO_InitStruct.Pin = GPIO_PIN_13;
  GPIO_InitStruct.Mode = GPIO_MODE_INPUT;
  GPIO_InitStruct.Pull = GPIO_PULLDOWN;
  HAL_GPIO_Init(GPIOC, &GPIO_InitStruct);

  /* USER CODE BEGIN MX_GPIO_Init_2 */

  /* USER CODE END MX_GPIO_Init_2 */
}

/* USER CODE BEGIN 4 */
uint8_t IsMetadataValid(void)
{
    const ApplicationMetadata *metadata =
        (const ApplicationMetadata *)METADATA_ADDRESS;

    if (metadata->magicNumber != METADATA_MAGIC)
        return 0;

    if (metadata->validMarker != APP_VALID_MARKER)
        return 0;

    if (metadata->firmwareSize == 0U ||
        metadata->firmwareSize > APP_MAX_SIZE)
        return 0;

    uint32_t calculatedCRC =
        CalculateCRC32(APP_ADDRESS, metadata->firmwareSize);

    if (calculatedCRC != metadata->firmwareCRC)
        return 0;

    return 1;
}

HAL_StatusTypeDef WriteApplicationMetadata(uint32_t firmwareSize,
                                           uint32_t firmwareCRC)
{
	if ((firmwareSize == 0U) ||
	    (firmwareSize > APP_MAX_SIZE))
	{
	    return HAL_ERROR;
	}

    HAL_StatusTypeDef status;
    uint32_t sectorError = 0xFFFFFFFFU;

    FLASH_EraseInitTypeDef eraseInit = {0};

    status = HAL_FLASH_Unlock();

    if (status != HAL_OK)
        return status;

    /* Erase metadata sector 4 only */
    eraseInit.TypeErase = FLASH_TYPEERASE_SECTORS;
    eraseInit.Banks = FLASH_BANK_1;
    eraseInit.Sector = FLASH_SECTOR_4;
    eraseInit.NbSectors = 1;
    eraseInit.VoltageRange = FLASH_VOLTAGE_RANGE_3;

    status = HAL_FLASHEx_Erase(&eraseInit, &sectorError);

    if (status != HAL_OK)
    {
        HAL_FLASH_Lock();
        return status;
    }

    /* Write metadata fields */
    status = HAL_FLASH_Program(
        FLASH_TYPEPROGRAM_WORD,
        METADATA_ADDRESS,
        METADATA_MAGIC
    );

    if (status == HAL_OK)
    {
        status = HAL_FLASH_Program(
            FLASH_TYPEPROGRAM_WORD,
            METADATA_ADDRESS + 4U,
            firmwareSize
        );
    }

    if (status == HAL_OK)
    {
        status = HAL_FLASH_Program(
            FLASH_TYPEPROGRAM_WORD,
            METADATA_ADDRESS + 8U,
            firmwareCRC
        );
    }

    /* Write valid marker LAST */
    if (status == HAL_OK)
    {
        status = HAL_FLASH_Program(
            FLASH_TYPEPROGRAM_WORD,
            METADATA_ADDRESS + 12U,
            APP_VALID_MARKER
        );
    }

    HAL_FLASH_Lock();

    return status;
}

HAL_StatusTypeDef InvalidateApplicationMetadata(void)
{
    HAL_StatusTypeDef status;
    uint32_t sectorError = 0xFFFFFFFFU;

    FLASH_EraseInitTypeDef eraseInit = {0};

    status = HAL_FLASH_Unlock();

    if (status != HAL_OK)
        return status;

    eraseInit.TypeErase = FLASH_TYPEERASE_SECTORS;
    eraseInit.Banks = FLASH_BANK_1;
    eraseInit.Sector = FLASH_SECTOR_4;
    eraseInit.NbSectors = 1;
    eraseInit.VoltageRange = FLASH_VOLTAGE_RANGE_3;

    status = HAL_FLASHEx_Erase(&eraseInit, &sectorError);

    HAL_FLASH_Lock();

    return status;
}

HAL_StatusTypeDef ProgramApplicationFlash(uint32_t offset,
                                          uint8_t *data,
                                          uint16_t length)
{
    if ((data == NULL) || (length == 0U))
    {
        return HAL_ERROR;
    }

    if (((offset & 0x03U) != 0U) ||
        (offset > APP_MAX_SIZE) ||
        (length > (APP_MAX_SIZE - offset)))
    {
        return HAL_ERROR;
    }

    HAL_StatusTypeDef status = HAL_FLASH_Unlock();

    if (status != HAL_OK)
    {
        return status;
    }

    uint32_t address = APP_ADDRESS + offset;
    uint16_t index = 0;

    while (index < length)
    {
        uint8_t bytes[4] = {0xFF, 0xFF, 0xFF, 0xFF};

        uint16_t remaining = length - index;
        uint16_t bytesToWrite = (remaining >= 4U) ? 4U : remaining;

        memcpy(bytes, &data[index], bytesToWrite);

        uint32_t word =
            ((uint32_t)bytes[0])       |
            ((uint32_t)bytes[1] << 8)  |
            ((uint32_t)bytes[2] << 16) |
            ((uint32_t)bytes[3] << 24);

        status = HAL_FLASH_Program(FLASH_TYPEPROGRAM_WORD,
                                   address,
                                   word);

        if (status != HAL_OK)
        {
            break;
        }

        address += 4U;
        index += bytesToWrite;
    }

    HAL_FLASH_Lock();

    return status;
}

uint8_t IsDuplicatePacket(uint32_t offset,
                          uint8_t *data,
                          uint16_t length)
{
    /* Validate input parameters and Flash boundaries */
    if ((data == NULL) ||
        (length == 0U) ||
        ((offset & 0x03U) != 0U) ||
        (offset > APP_MAX_SIZE) ||
        ((uint32_t)length > (APP_MAX_SIZE - offset)))
    {
        return 0U;
    }

    /* No previously accepted packet */
    if (lastPacketValid == 0U)
    {
        return 0U;
    }

    /* Check whether offset and length match */
    if ((offset != lastAcceptedOffset) ||
        (length != lastAcceptedLength))
    {
        return 0U;
    }

    /* Compare received data with data already stored in Flash */
    const uint8_t *flashData =
        (const uint8_t *)(APP_ADDRESS + offset);

    for (uint16_t i = 0U; i < length; i++)
    {
        if (flashData[i] != data[i])
        {
            return 0U;
        }
    }

    return 1U;
}

void SendBootloaderResponse(uint8_t response)
{
    HAL_UART_Transmit(&huart3,
                      &response,
                      1,
                      HAL_MAX_DELAY);
}

uint32_t CalculateCRC32(uint32_t address, uint32_t length)
{
    uint32_t crc = 0xFFFFFFFFU;

    const uint8_t *data = (const uint8_t *)address;

    for (uint32_t i = 0; i < length; i++)
    {
        crc ^= data[i];

        for (uint8_t bit = 0; bit < 8; bit++)
        {
            if (crc & 1U)
            {
                crc = (crc >> 1) ^ 0xEDB88320U;
            }
            else
            {
                crc >>= 1;
            }
        }
    }

    return crc ^ 0xFFFFFFFFU;
}

HAL_StatusTypeDef EraseApplicationFlash(uint32_t *failedSector)
{
	if (failedSector == NULL)
	{
	    return HAL_ERROR;
	}

    FLASH_EraseInitTypeDef EraseInitStruct = {0};
    uint32_t SectorError = 0;

    *failedSector = 0xFFFFFFFFU;

    // Unlock Flash
    HAL_StatusTypeDef status = HAL_FLASH_Unlock();

    if (status != HAL_OK)
    {
        return status;
    }

    // Configure Bank 1 erase: Sectors 5–11
    EraseInitStruct.TypeErase = FLASH_TYPEERASE_SECTORS;
    /*EraseInitStruct.Banks = FLASH_BANK_1;*/
    EraseInitStruct.Sector = FLASH_SECTOR_5;
    EraseInitStruct.NbSectors = 7;
    EraseInitStruct.VoltageRange = FLASH_VOLTAGE_RANGE_3;

    // Erase Bank 1
    status = HAL_FLASHEx_Erase(&EraseInitStruct, &SectorError);

    *failedSector = SectorError;

    if (status != HAL_OK)
    {
        HAL_FLASH_Lock();
        return status;
    }

    // Configure Bank 2 erase: Sectors 12–23
   /* EraseInitStruct.Banks = FLASH_BANK_2;*/
    EraseInitStruct.Sector = FLASH_SECTOR_12;
    EraseInitStruct.NbSectors = 12;

    // Reset error information
    SectorError = 0xFFFFFFFFU;

    // Erase Bank 2
    status = HAL_FLASHEx_Erase(&EraseInitStruct, &SectorError);

    *failedSector = SectorError;

    // Lock Flash after operations
    HAL_FLASH_Lock();

    return status;
}

uint8_t ReceivePacket(void)
  {
      // Step 1: Receive start byte
	if (HAL_UART_Receive(&huart3, &startByte, 1, HAL_MAX_DELAY) != HAL_OK)
	{
	    return 0;
	}

      // Step 2: Validate start byte
      if (startByte != BOOT_START_BYTE)
      {
          return 0;
      }

      // Step 3: Receive command ID
      if (HAL_UART_Receive(&huart3, &commandID, 1, HAL_MAX_DELAY) != HAL_OK)
      {
          return 0;
      }

      // Step 4: Receive payload length
      if (HAL_UART_Receive(&huart3, &payloadLength, 1, HAL_MAX_DELAY) != HAL_OK)
      {
          return 0;
      }

      // Step 5: Validate payload length
      if (payloadLength > MAX_PAYLOAD_SIZE)
      {
          return 0;
      }

      // Step 6: Receive payload
      if (payloadLength > 0)
      {
          if (HAL_UART_Receive(&huart3,
                               rxBuffer,
                               payloadLength,
                               HAL_MAX_DELAY) != HAL_OK)
          {
              return 0;
          }
      }

      return 1;
  }

uint8_t IsBootloaderButtonPressed(void)
{
    return (HAL_GPIO_ReadPin(GPIOC, GPIO_PIN_13) == GPIO_PIN_SET);
}

void Bootloader_CheckAndBootApplication(void)
{
    if (IsBootloaderButtonPressed())
    {
        // USER button pressed: Stay in bootloader
        return;
    }

    if (IsApplicationValid())
    {
        // Valid application found: Boot application
        Bootloader_Cleanup();
        JumpToApplication();
    }

    // Invalid application: Stay in bootloader
}

__attribute__((naked, noreturn))
void JumpToApplication(void)
{
    __asm volatile
    (
        "cpsid i             \n"

        "ldr r0, =0x08020000 \n"
        "ldr r1, [r0]        \n"
        "ldr r2, [r0, #4]    \n"

        "ldr r3, =0xE000ED08 \n"
        "str r0, [r3]        \n"

        "dsb                 \n"
        "isb                 \n"

        "movs r3, #0         \n"
        "msr basepri, r3     \n"
        "msr faultmask, r3   \n"
        "msr control, r3     \n"
        "isb                 \n"

        "msr msp, r1         \n"
        "bx r2               \n"
    );
}
void Bootloader_Cleanup(void)
{
    // Disable global interrupts
    __disable_irq();

    // Stop SysTick timer
    SysTick->CTRL = 0;
    SysTick->LOAD = 0;
    SysTick->VAL = 0;

    // Disable and clear all external NVIC interrupts
    for (uint32_t i = 0; i < 8; i++)
    {
        NVIC->ICER[i] = 0xFFFFFFFF;
        NVIC->ICPR[i] = 0xFFFFFFFF;
    }

    // Clear pending system exceptions
    SCB->ICSR = SCB_ICSR_PENDSTCLR_Msk |
                SCB_ICSR_PENDSVCLR_Msk;
}
/* USER CODE END 4 */

/**
  * @brief  This function is executed in case of error occurrence.
  * @retval None
  */
void Error_Handler(void)
{
  /* USER CODE BEGIN Error_Handler_Debug */
  /* User can add his own implementation to report the HAL error return state */
  __disable_irq();
  while (1)
  {
  }
  /* USER CODE END Error_Handler_Debug */
}
#ifdef USE_FULL_ASSERT
/**
  * @brief  Reports the name of the source file and the source line number
  *         where the assert_param error has occurred.
  * @param  file: pointer to the source file name
  * @param  line: assert_param error line source number
  * @retval None
  */
void assert_failed(uint8_t *file, uint32_t line)
{
  /* USER CODE BEGIN 6 */
  /* User can add his own implementation to report the file name and line number,
     ex: printf("Wrong parameters value: file %s on line %d\r\n", file, line) */
  /* USER CODE END 6 */
}
#endif /* USE_FULL_ASSERT */

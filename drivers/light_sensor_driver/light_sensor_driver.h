#define I2C_MASTER_NUM           I2C_NUM_0
#define I2C_MASTER_SDA_IO        21       // đổi theo chân bạn muốn
#define I2C_MASTER_SCL_IO        22
#define I2C_MASTER_FREQ_HZ       100000   // 100kHz
#define I2C_MASTER_TX_BUF_DISABLE 0
#define I2C_MASTER_RX_BUF_DISABLE 0

#define BH1750_ADDR 0x23
#define CMD_START 0x10

#pragma once

#include "esp_err.h"

#ifdef __cplusplus
extern "C" {
#endif

/**
 * @brief Khởi tạo i2c mode
 */
esp_err_t i2c_init(void);

/**
 * @brief Khởi tạo light sensor
 */
esp_err_t bh1750_init(void);

/**
 * @brief Đọc giá trị sensor
 */
float bh1750_read_lux();

#ifdef __cplusplus
}
#endif
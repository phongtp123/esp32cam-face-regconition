#define MOTION_GPIO 12

#pragma once

#include "esp_err.h"

#ifdef __cplusplus
extern "C" {
#endif

/**
 * @brief Khởi tạo motion sensor
 */
esp_err_t motion_init(void);

/**
 * @brief Đọc giá trị sensor
 */
int motion_read(void);

#ifdef __cplusplus
}
#endif
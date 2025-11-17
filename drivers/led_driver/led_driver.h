#define LED_STRIP_GPIO        26
#define LED_STRIP_LENGTH      8

#pragma once

#include "esp_err.h"

#ifdef __cplusplus
extern "C" {
#endif

/**
 * @brief Khởi tạo LED
 */
esp_err_t led_init(void);

/**
 * @brief Bật LED
 */
void led_on(void);

/**
 * @brief Tắt LED
 */
void led_off(void);

#ifdef __cplusplus
}
#endif
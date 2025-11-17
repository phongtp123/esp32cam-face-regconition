#define LED_GPIO    4


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
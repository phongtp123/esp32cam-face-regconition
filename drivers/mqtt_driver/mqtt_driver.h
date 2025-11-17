#define CONFIG_BROKER_URL "mqtt://10.197.209.70:1884"

#pragma once

#include "esp_err.h"

#ifdef __cplusplus
extern "C" {
#endif

/**
 * @brief Khởi chạy mqtt
 */
esp_err_t mqtt_app_start(void);

#ifdef __cplusplus
}
#endif
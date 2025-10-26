#define CONFIG_BROKER_URL "mqtts://10.72.180.70"

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
#define LIGHT_ESP_WIFI_SSID     "Redmi12"
#define LIGHT_ESP_WIFI_PASS     "12345678"
#define LIGHT_ESP_MAXIMUM_RETRY 5

#pragma once

#include "esp_err.h"

#ifdef __cplusplus
extern "C" {
#endif

/**
 * @brief Khởi tạo Wi-Fi
 */
esp_err_t wifi_initialize(void);

/**
 * @brief Khởi tạo Wi-Fi Provisioning
 */
esp_err_t wifi_station_initialize(void);

#ifdef __cplusplus
}
#endif
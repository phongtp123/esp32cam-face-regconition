#include <esp_log.h>

#include "wifi_driver.h"
#include "mqtt_driver.h"

#include "nvs_flash.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h" 
#include "led_test_driver.h"

static const char *TAG = "Control light";

void app_main(void)
{
    esp_err_t err;

    esp_err_t ret = nvs_flash_init(); // khởi tạo nvs

    if (ret == ESP_ERR_NVS_NO_FREE_PAGES || ret == ESP_ERR_NVS_NEW_VERSION_FOUND) {
        ESP_ERROR_CHECK(nvs_flash_erase());
        ret = nvs_flash_init();
    }

    ESP_ERROR_CHECK(ret);

    led_test_init(); 
    wifi_initialize(); // khởi tạo wifi 

    err = wifi_station_initialize();
    if (err != ESP_OK) {
        ESP_LOGE(TAG, "Could not start Wifi. Aborting!!!");
        vTaskDelay(pdMS_TO_TICKS(5000));
        abort();
    } else {
        led1_on(); 
    }

    err = mqtt_app_start(); // khởi tạo mqtt app - để gửi hoặc nhận dữ liệu
    if (err != ESP_OK) {
        ESP_LOGE(TAG, "Could not start MQTT service");
        vTaskDelay(pdMS_TO_TICKS(5000));
        abort();
    } else {
        led2_on(); 
    }


    // while (1) {
    //     led1_on(); 
    //     led2_on(); 
    //     vTaskDelay(pdMS_TO_TICKS(100)); 

    //     led1_off(); 
    //     led2_off(); 
    //     vTaskDelay(pdMS_TO_TICKS(100)); 
    // }

}
#include "driver/rmt_tx.h"
#include "driver/gpio.h"
#include "esp_log.h"

#include "led_driver.h"

static const char *TAG = "LED_Driver";

esp_err_t led_init(void){
    gpio_config_t led_gpio = {
        .pin_bit_mask = 1ULL << LED_GPIO,
        .mode = GPIO_MODE_OUTPUT,
        .pull_up_en = GPIO_PULLUP_DISABLE,
        .pull_down_en = GPIO_PULLDOWN_DISABLE,
        .intr_type = GPIO_INTR_DISABLE,
    };
    esp_err_t ret = gpio_config(&led_gpio);
    ESP_LOGI(TAG, "LED initialized on GPIO %d", LED_GPIO);
    return ret;
}

void led_on(void){
    gpio_set_level(LED_GPIO, 1);
    ESP_LOGI(TAG, "LED bật");
}

void led_off(void){
    gpio_set_level(LED_GPIO, 0);
    ESP_LOGI(TAG, "LED tắt");
}
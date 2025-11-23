#include "esp_log.h"
#include "driver/gpio.h"
#include <string.h>
#include "led_test_driver.h"

static const char *TAG = "LED_DRIVER"; 



void led_test_init(void) {
    gpio_reset_pin(LED_TEST_1);
    gpio_set_direction(LED_TEST_1, GPIO_MODE_OUTPUT); 
    gpio_reset_pin(LED_TEST_2);
    gpio_set_direction(LED_TEST_2, GPIO_MODE_OUTPUT); 

    ESP_LOGI(TAG, "INIT THÀNH CÔNG"); 
}

void led1_on(void) {
    gpio_set_level(LED_TEST_1, 1);
    ESP_LOGI(TAG, " LED 1 SÁNG");
}

void led1_off(void) {
    gpio_set_level(LED_TEST_1, 0);
    ESP_LOGI(TAG, "LED 1 TẮT"); 
}

void led2_on(void) {
    gpio_set_level(LED_TEST_2, 1);
    ESP_LOGI(TAG, "LED 2 SÁNG");
}

void led2_off(void) {
    gpio_set_level(LED_TEST_2, 0);
    ESP_LOGI(TAG, "LED 2 TẮT"); 
}



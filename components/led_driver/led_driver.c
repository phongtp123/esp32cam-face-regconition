#include "esp_log.h"
#include "driver/gpio.h"
#include "mqtt_driver.h"
#include <string.h>
#include "cJSON.h"
#include "led_driver.h"

static const char *TAG = "LED_DRIVER"; 



static void led_init(void) {
    gpio_reset_pin(LED_PIN);
    gpio_set_direction(LED_PIN, GPIO_MODE_OUTPUT); 
    ESP_LOGI(TAG, "INIT THÀNH CÔNG"); 
}

static void led_on(void) {
    gpio_set_level(LED_PIN, 1);
    ESP_LOGI(TAG, "SÁNG");
}

static void led_off(void) {
    gpio_set_level(LED_PIN, 0);
    ESP_LOGI(TAG, "TẮT"); 
}



// đây là hàm điều khiển led 
static void led_mqtt_callback(const char *topic, const char *data, int len) 
{
    ESP_LOGI(TAG, "Callback LED, topic='%s', raw data='%.*s'", topic, len, data);

    if (strcmp(topic, WORKING_TOPIC) != 0)
        return;

    // CHUYỂN MQTT PAYLOAD → CHUỖI C
    char buf[32];
    if (len >= sizeof(buf)) len = sizeof(buf) - 1;
    memcpy(buf, data, len);
    buf[len] = '\0';

    if (strcmp(buf, "1") == 0) {
        led_on();
    } else {
        led_off();
    }
}



void led_control_init(void) {
    led_init(); 

    // led_off(); 

    mqtt_register_callback(led_mqtt_callback); 
}


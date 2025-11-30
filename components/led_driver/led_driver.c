#include "esp_log.h"
#include "driver/gpio.h"
#include "mqtt_driver.h"
#include <string.h>
#include "led_driver.h"
#include "cJSON.h"

static const char *TAG = "LIGHT_DRIVER"; 



static void led_init(void) {
    gpio_reset_pin(LED_PIN);
    gpio_set_direction(LED_PIN, GPIO_MODE_OUTPUT); 
    ESP_LOGI(TAG, "INIT THÀNH CÔNG"); 
}

static void led_on(void) {
    gpio_set_level(LED_PIN, 1);
    ESP_LOGI(TAG, "ĐÈN SÁNG");
}

static void led_off(void) {
    gpio_set_level(LED_PIN, 0);
    ESP_LOGI(TAG, "ĐÈN TẮT"); 
}



// đây là hàm điều khiển led 
static void led_mqtt_callback(const char *topic, int topic_len, const char *data, int data_len)
{
    ESP_LOGI(TAG, "Topic = '%.*s'", topic_len, topic);
    ESP_LOGI(TAG, "Data  = '%.*s'", data_len, data);

    // So sánh topic chuẩn
    if (strncmp(topic, WORKING_TOPIC, topic_len) != 0 ||
        topic_len != strlen(WORKING_TOPIC))
    {
        ESP_LOGW(TAG, "Topic không khớp!");
        return;
    }


    ESP_LOGI(TAG, "Đúng topic"); 
    // Parse JSON
    cJSON *root = cJSON_ParseWithLength(data, data_len);
    if (!root) {
        ESP_LOGE(TAG, "JSON parse error!");
        return;
    }

    cJSON *switch_p = cJSON_GetObjectItem(root, "switch");

    if (cJSON_IsNumber(switch_p)) {
        if (switch_p->valueint == 1) {
            led_on();
        } else {
            led_off();
        }
    } else {
        ESP_LOGE(TAG, "No 'status' field in JSON!");
    }

    cJSON_Delete(root);
}




void led_control_init(void) {
    led_init(); 

    // led_off(); 

    mqtt_register_callback(led_mqtt_callback); 
}


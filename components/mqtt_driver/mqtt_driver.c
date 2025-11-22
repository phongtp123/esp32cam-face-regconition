#include "esp_log.h"
#include "nvs_flash.h"
#include "wifi_driver.h"
#include "esp_err.h"
#include "mqtt_client.h"
#include <stdint.h>
#include <stdio.h>
#include "mqtt_driver.h"

static const char *TAG = "MQTT CLIENT";

static esp_mqtt_client_handle_t client = NULL;
static mqtt_message_callback_t mqtt_cb = NULL; 



void mqtt_register_callback(mqtt_message_callback_t cb) 
{
    mqtt_cb = cb; 
}




/*****************************
 * ĐỂ CẤU HÌNH CHO MQTT THÌ CÓ CÁC BƯỚC SAU 
 * 
 * 
 */
// ==== TẠO EVENT HANDLER ==== GIỐNG NHƯ VỚI WIFI - ĐÂY LÀ TRÁI TIM CỦA NÓ 
// mình nghĩ đây là bước làm sau khi đã config xong 
static esp_err_t mqtt_event_handler_cb(esp_mqtt_event_handle_t event) 
{
    switch (event->event_id) {
        
        case (MQTT_EVENT_CONNECTED):
            ESP_LOGI(TAG, "MQTT connected"); 

            // subcribe ngay sau khi kết nối
            esp_mqtt_client_subscribe(client, "esp32c3/test", 1); 
            esp_mqtt_client_subscribe(client, WORKING_TOPIC, 1); 
            // esp_mqtt_client_publish(client, WORKING_TOPIC, "0", 0, 1, 1); 

            // pubblish 1 message test 

            esp_mqtt_client_publish(client, "esp/32c3/status", "Hello!", 0, 1, 0);
            break;

        case (MQTT_EVENT_DATA):
            ESP_LOGI(TAG, "received message:\n"); 
            printf("Topic: %.*s\n", event->topic_len, event->topic); 
            printf("Data: %.*s\n", event->data_len, event->data); 

            if (mqtt_cb) {
                mqtt_cb(event->topic, event->data, event->data_len); 
            }

            break; 

        default:
            break;

    }

    return ESP_OK; 
}

// kết hợp với bước trên 
static void mqtt_event_handler(void *handler_args, esp_event_base_t base, int32_t event_id, void *event_data) 
{
    mqtt_event_handler_cb(event_data); 
}


void mqtt_pub(char *topic, char *msg) {
    esp_mqtt_client_publish(client, topic, msg, 0, 1, 1); 
}




void mqtt_init(void)
{
    //
    nvs_flash_init(); 

    wifi_start(); 

    esp_mqtt_client_config_t mqtt_cfg = {
        .broker.address.uri = BROKER_ADDR_URI,
    };

    vTaskDelay(pdMS_TO_TICKS(5000)); 

    // init MQTT
    client = esp_mqtt_client_init(&mqtt_cfg); 
    ESP_LOGI(TAG, "init MQTT successfully"); 

    // register event 
    esp_mqtt_client_register_event(client, ESP_EVENT_ANY_ID, mqtt_event_handler, NULL); 
    ESP_LOGI(TAG, "register MQTT event handler successfully"); 

    // START mqtt
    esp_mqtt_client_start(client);
    ESP_LOGI(TAG, "start MQTT successfully"); 

}

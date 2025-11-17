#include "mqtt_client.h"
#include "esp_log.h"

#include "mqtt_driver.h"
#include "led_driver.h"

#include "cJSON.h"

static const char *TAG = "MQTT";
static esp_mqtt_client_handle_t mqtt_client_handle = NULL;

static bool night_time = false;

static void log_error_if_nonzero(const char * message, int error_code)
{
    if (error_code != 0) {
        ESP_LOGE(TAG, "Last error %s: 0x%x", message, error_code);
    }
}

static void handle_motion_message(const char *data, int len)
{
    cJSON *root = cJSON_ParseWithLength(data, len);
    if (!root) {
        ESP_LOGW(TAG, "Không parse được JSON: %.*s", len, data);
        return;
    }

    cJSON *status = cJSON_GetObjectItem(root, "status");
    if (cJSON_IsNumber(status)) {
        if (status->valueint == 1 && night_time) {
            led_on();
        } else {
            led_off();
        }
    } else {
        ESP_LOGW(TAG, "Không tìm thấy trường 'status' hợp lệ");
    }

    cJSON_Delete(root);
}

static void handle_light_sensor_message(const char *data, int len)
{
    cJSON *root = cJSON_ParseWithLength(data, len);
    if (!root) {
        ESP_LOGW(TAG, "Không parse được JSON: %.*s", len, data);
        return;
    }

    cJSON *status = cJSON_GetObjectItem(root, "status");
    if (cJSON_IsNumber(status)) {
        if (status->valueint == 1) {
            night_time = true;
        } else {
            night_time = false;
        }
    } else {
        ESP_LOGW(TAG, "Không tìm thấy trường 'status' hợp lệ");
    }

    cJSON_Delete(root);
}

static esp_err_t mqtt_event_handler_cb(esp_mqtt_event_handle_t event)
{
    esp_mqtt_client_handle_t client = event->client;
    int msg_id_1, msg_id_2;
    
    switch (event->event_id) {
        case MQTT_EVENT_CONNECTED:
            ESP_LOGI(TAG, "MQTT_EVENT_CONNECTED");
            msg_id_1 = esp_mqtt_client_subscribe(client, "/motion/status", 0);
            ESP_LOGI(TAG, "Subscribed to /motion/status (msg_id=%d)", msg_id_1);
            msg_id_2 = esp_mqtt_client_subscribe(client, "/lsensor/status", 0);
            ESP_LOGI(TAG, "Subscribed to /lsensor/status (msg_id=%d)", msg_id_2);
            break;
        case MQTT_EVENT_DISCONNECTED:
            ESP_LOGI(TAG, "MQTT_EVENT_DISCONNECTED");
            break;
        case MQTT_EVENT_SUBSCRIBED:
            ESP_LOGI(TAG, "MQTT_EVENT_SUBSCRIBED, msg_id=%d", event->msg_id);
            break;
        case MQTT_EVENT_UNSUBSCRIBED:
            ESP_LOGI(TAG, "MQTT_EVENT_UNSUBSCRIBED, msg_id=%d", event->msg_id);
            break;
        case MQTT_EVENT_PUBLISHED:
            ESP_LOGI(TAG, "MQTT_EVENT_PUBLISHED, msg_id=%d", event->msg_id);
            break;
        case MQTT_EVENT_DATA:
            ESP_LOGI(TAG, "MQTT_EVENT_DATA");
            printf("TOPIC=%.*s\r\n", event->topic_len, event->topic);
            printf("DATA=%.*s\r\n", event->data_len, event->data);
            if (strncmp(event->topic, "/motion/status", event->topic_len) == 0) {
                handle_motion_message(event->data, event->data_len);
            }

            if (strncmp(event->topic, "/lsensor/status", event->topic_len) == 0) {
                handle_light_sensor_message(event->data, event->data_len);
            }
            break;
        case MQTT_EVENT_ERROR:
            ESP_LOGI(TAG, "MQTT_EVENT_ERROR");
            if (event->error_handle->error_type == MQTT_ERROR_TYPE_TCP_TRANSPORT) {
                log_error_if_nonzero("reported from esp-tls", event->error_handle->esp_tls_last_esp_err);
                log_error_if_nonzero("reported from tls stack", event->error_handle->esp_tls_stack_err);
                log_error_if_nonzero("captured as transport's socket errno",  event->error_handle->esp_transport_sock_errno);
                ESP_LOGI(TAG, "Last errno string (%s)", strerror(event->error_handle->esp_transport_sock_errno));

            }
            break;
        default:
            ESP_LOGI(TAG, "Other event id:%d", event->event_id);
            break;
    }
    return ESP_OK;
}

static void mqtt_event_handler(void *handler_args, esp_event_base_t base, int32_t event_id, void *event_data) {
    ESP_LOGD(TAG, "Event dispatched from event loop base=%s, event_id=%d", base, event_id);
    mqtt_event_handler_cb(event_data);
}

esp_err_t mqtt_app_start(void)
{
    // extern const uint8_t client_cert_pem_start[] asm("_binary_client_crt_start");
    // extern const uint8_t client_cert_pem_end[] asm("_binary_client_crt_end");
    // extern const uint8_t client_key_pem_start[] asm("_binary_client_key_start");
    // extern const uint8_t client_key_pem_end[] asm("_binary_client_key_end");
    // extern const uint8_t server_cert_pem_start[] asm("_binary_ca_crt_start");
    // extern const uint8_t server_cert_pem_end[] asm("_binary_ca_crt_end");
    
    esp_mqtt_client_config_t mqtt_cfg = {
        .broker = {
            .address.uri = CONFIG_BROKER_URL,
            // .verification.certificate = (const char *)server_cert_pem_start,
        },
        // .credentials = {
        //     .authentication = {
        //         .certificate = (const char *)client_cert_pem_start,
        //         .key = (const char *)client_key_pem_start,
        //     },
        // },
    };

    mqtt_client_handle = esp_mqtt_client_init(&mqtt_cfg);

    esp_mqtt_client_register_event(mqtt_client_handle, ESP_EVENT_ANY_ID, mqtt_event_handler, mqtt_client_handle);

    esp_mqtt_client_start(mqtt_client_handle);

    led_init();

    return ESP_OK;
}
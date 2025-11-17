#include "motion_driver.h"
#include "driver/gpio.h"
#include "esp_log.h"

static const char *TAG = "MOTION";

esp_err_t motion_init(void)
{
    gpio_config_t io_conf = {
        .pin_bit_mask = 1ULL << MOTION_GPIO,
        .mode = GPIO_MODE_INPUT,
        .pull_up_en = GPIO_PULLUP_ENABLE,
        .pull_down_en = GPIO_PULLDOWN_DISABLE,
        .intr_type = GPIO_INTR_DISABLE,
    };
    esp_err_t ret = gpio_config(&io_conf);
    ESP_LOGI(TAG, "PIR Motion sensor initialized on GPIO %d", MOTION_GPIO);
    return ret;
}

int motion_read(void)
{
    return gpio_get_level(MOTION_GPIO);
}
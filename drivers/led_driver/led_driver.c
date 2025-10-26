#include "led_strip.h"
#include "driver/rmt_tx.h"
#include "esp_log.h"

#include "led_driver.h"

static const char *TAG = "LED_Driver";
static led_strip_handle_t led_strip = NULL;

esp_err_t led_init(void)
{
    led_strip_config_t strip_config = {
        .strip_gpio_num = LED_STRIP_GPIO,
        .max_leds = LED_STRIP_LENGTH,
    };
    led_strip_rmt_config_t rmt_config = {
        .resolution_hz = 10 * 1000 * 1000, // 10 MHz
    };
    ESP_ERROR_CHECK(led_strip_new_rmt_device(&strip_config, &rmt_config, &led_strip));
    ESP_LOGI(TAG, "LED strip đã khởi tạo thành công");
    return ESP_OK;
}

void led_on(void)
{
    for (int i = 0; i < LED_STRIP_LENGTH; i++) {
        led_strip_set_pixel(led_strip, i, 0, 255, 0); // G màu xanh
    }
    led_strip_refresh(led_strip);
    ESP_LOGI(TAG, "LED bật");
}

void led_off(void)
{
    led_strip_clear(led_strip);
    ESP_LOGI(TAG, "LED tắt");
}

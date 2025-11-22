#include "esp_log.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "mqtt_driver.h"
#include "led_driver.h"

static const char *TAG = "LED CONTROL"; 

void app_main(void)
{
    mqtt_init(); 

    led_control_init(); 
}

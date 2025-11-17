#include "light_sensor_driver.h"
#include "driver/i2c.h"
#include "esp_log.h"

static const char *TAG = "LIGHT_SENSOR";

esp_err_t i2c_init(void){
    esp_err_t ret = ESP_OK;

    i2c_config_t conf = {
        .mode = I2C_MODE_MASTER,
        .sda_io_num = I2C_MASTER_SDA_IO,
        .sda_pullup_en = GPIO_PULLUP_ENABLE,
        .scl_io_num = I2C_MASTER_SCL_IO,
        .scl_pullup_en = GPIO_PULLUP_ENABLE,
        .master.clk_speed = I2C_MASTER_FREQ_HZ,
    };

    ret = i2c_param_config(I2C_MASTER_NUM, &conf);
    ret = i2c_driver_install(I2C_MASTER_NUM, conf.mode, I2C_MASTER_RX_BUF_DISABLE, I2C_MASTER_TX_BUF_DISABLE, 0);
    if(ret == ESP_OK){
        ESP_LOGI(TAG, "I2C initialized successfully");
        return ret;
    }
    ESP_LOGI(TAG, "I2C initialized failed!");
    return ret;
}

esp_err_t bh1750_init(void) {
    uint8_t cmd = CMD_START;
    esp_err_t ret = ESP_OK;
    ret = i2c_master_write_to_device(I2C_MASTER_NUM, BH1750_ADDR, &cmd, 1, 1000);
    if(ret == ESP_OK){
        ESP_LOGI(TAG, "BH1750 init OK"); 
        return ret;
    }
    ESP_LOGI(TAG, "BH1750 init failed"); 
    return ret;
}

float bh1750_read_lux(){
    uint8_t data[2];
    ESP_ERROR_CHECK(i2c_master_read_from_device(I2C_MASTER_NUM, BH1750_ADDR, data, 2, 1000));
    uint16_t raw = (data[0] << 8) | data[1];
    return raw / 1.2;
}
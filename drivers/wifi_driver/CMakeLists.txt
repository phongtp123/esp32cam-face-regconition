idf_component_register(SRCS "wifi_driver.c"
                      INCLUDE_DIRS "."
                      REQUIRES esp_wifi esp_event esp_system nvs_flash freertos
                            lwip wifi_provisioning qrcode)
idf_component_register(SRCS "mqtt_driver.c"
                      INCLUDE_DIRS "."
                      REQUIRES nvs_flash wifi_driver mqtt)
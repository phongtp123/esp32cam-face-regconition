idf_component_register(SRCS "control_led.c"
                        PRIV_INCLUDE_DIRS "."
                        REQUIRES wifi_driver mqtt_driver nvs_flash freertos
                        ) 

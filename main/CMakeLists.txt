idf_component_register(SRCS "led-control.c"
                    INCLUDE_DIRS "."
                    REQUIRES mqtt_driver led_driver)

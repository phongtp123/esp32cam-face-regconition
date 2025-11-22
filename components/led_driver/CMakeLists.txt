idf_component_register(SRCS "led_driver.c"
                      INCLUDE_DIRS "."
                      REQUIRES mqtt_driver json driver)
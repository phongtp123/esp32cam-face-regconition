idf_component_register(SRCS "mqtt_driver.c"
                      INCLUDE_DIRS "."
                      PRIV_REQUIRES mqtt led_driver
                      EMBED_TXTFILES "ca.crt" "client.crt" "client.key")
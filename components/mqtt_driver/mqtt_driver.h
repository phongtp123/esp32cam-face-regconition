#define BROKER_ADDR_URI "mqtt://10.54.117.6:1883"
#define WORKING_TOPIC "switch/status"

#pragma once


#include "mqtt_client.h"

typedef void (*mqtt_message_callback_t)(const char *topic, int topic_len, const char *data, int data_len);



void mqtt_init(void); 

void mqtt_publish_json(const char*, int); 

void mqtt_register_callback(mqtt_message_callback_t);



#pragma once

#include "driver/gpio.h"

#define LED_TEST_1 GPIO_NUM_14
#define LED_TEST_2 GPIO_NUM_27

void led_test_init(void);

void led1_on(void);

void led1_off(void);

void led2_on(void);

void led2_off(void);
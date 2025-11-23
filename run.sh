#!/bin/bash
idf.py clean
idf.py build
idf.py -p /dev/ttyUSB0 flash monitor


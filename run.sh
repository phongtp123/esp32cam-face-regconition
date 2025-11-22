#!/bin/bash
idf.py clean 
idf.py build
idf.py -p /dev/ttyACM0 flash monitor


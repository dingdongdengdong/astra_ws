#!/bin/bash

candump vcan0 | cantools decode --single-line ../src/odrive_can/dbc/odrive-cansimple-0.5.6.dbc

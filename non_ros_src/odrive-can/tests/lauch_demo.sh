#!/usr/bin/env bash

# launch two mock nodes and two demo nodes.
# simulates a system conaining two drives.

INTERFACE="vcan0"

set -e

trap "kill 0" EXIT

odrive_can mock --axis-id 1 --interface $INTERFACE &
odrive_can mock --axis-id 2 --interface $INTERFACE &

odrive_can demo position --axis-id 1 --interface vcan0 --amplitude 20 &
odrive_can demo velocity --axis-id 2 --interface vcan0 &

wait


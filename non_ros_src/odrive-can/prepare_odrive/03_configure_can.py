#!/usr/bin/env python3
"""
 Set odrive can parameters

 Copyright (c) 2023 ROX Automation - Jev Kuznetsov
"""
import odrive  # type: ignore

drv = odrive.find_any()
print(f"Found ODrive {drv.serial_number}")


drv.axis0.config.can.node_id = 1
drv.axis0.config.can.encoder_rate_ms = 100
drv.axis0.config.can.heartbeat_rate_ms = 200


drv.axis1.config.can.node_id = 8
drv.axis1.config.can.encoder_rate_ms = 0
drv.axis1.config.can.heartbeat_rate_ms = 0

drv.can.config.baud_rate = 500000
drv.save_configuration()
drv.reboot()

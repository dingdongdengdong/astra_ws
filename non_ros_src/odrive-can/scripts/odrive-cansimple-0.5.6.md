## odrive-cansimple-0.5.6  interface

### ID: 1 - Axis0_Heartbeat
- Name: Axis0_Heartbeat
- Length: 8 bytes
- Sender: ['ODrive_Axis0']

| Signal Name | Start Bit | Length | Factor | Offset | Min Value | Max Value | Unit | Receiver | Choices |
|-------------|-----------|--------|--------|--------|-----------|-----------|------|----------|---------|
| Axis_Error | 0 | 32 | 1 | 0 | None | None |  | Master | 0: NONE, 1: INVALID_STATE, 64: MOTOR_FAILED, 128: SENSORLESS_ESTIMATOR_FAILED, 256: ENCODER_FAILED, 512: CONTROLLER_FAILED, 2048: WATCHDOG_TIMER_EXPIRED, 4096: MIN_ENDSTOP_PRESSED, 8192: MAX_ENDSTOP_PRESSED, 16384: ESTOP_REQUESTED, 131072: HOMING_WITHOUT_ENDSTOP, 262144: OVER_TEMP, 524288: UNKNOWN_POSITION |
| Axis_State | 32 | 8 | 1 | 0 | None | None |  | Master | 0: UNDEFINED, 1: IDLE, 2: STARTUP_SEQUENCE, 3: FULL_CALIBRATION_SEQUENCE, 4: MOTOR_CALIBRATION, 6: ENCODER_INDEX_SEARCH, 7: ENCODER_OFFSET_CALIBRATION, 8: CLOSED_LOOP_CONTROL, 9: LOCKIN_SPIN, 10: ENCODER_DIR_FIND, 11: HOMING, 12: ENCODER_HALL_POLARITY_CALIBRATION, 13: ENCODER_HALL_PHASE_CALIBRATION |
| Motor_Error_Flag | 40 | 1 | 1 | 0 | None | None |  | Master |  |
| Encoder_Error_Flag | 48 | 1 | 1 | 0 | None | None |  | Master |  |
| Controller_Error_Flag | 56 | 1 | 1 | 0 | None | None |  | Master |  |
| Trajectory_Done_Flag | 63 | 1 | 1 | 0 | None | None |  | Master |  |

### ID: 3 - Axis0_Get_Motor_Error
- Name: Axis0_Get_Motor_Error
- Length: 8 bytes
- Sender: ['ODrive_Axis0']

| Signal Name | Start Bit | Length | Factor | Offset | Min Value | Max Value | Unit | Receiver | Choices |
|-------------|-----------|--------|--------|--------|-----------|-----------|------|----------|---------|
| Motor_Error | 0 | 32 | 1 | 0 | None | None |  | Master | 0: NONE, 1: PHASE_RESISTANCE_OUT_OF_RANGE, 2: PHASE_INDUCTANCE_OUT_OF_RANGE, 8: DRV_FAULT, 16: CONTROL_DEADLINE_MISSED, 128: MODULATION_MAGNITUDE, 1024: CURRENT_SENSE_SATURATION, 4096: CURRENT_LIMIT_VIOLATION, 65536: MODULATION_IS_NAN, 131072: MOTOR_THERMISTOR_OVER_TEMP, 262144: FET_THERMISTOR_OVER_TEMP, 524288: TIMER_UPDATE_MISSED, 1048576: CURRENT_MEASUREMENT_UNAVAILABLE, 2097152: CONTROLLER_FAILED, 4194304: I_BUS_OUT_OF_RANGE, 8388608: BRAKE_RESISTOR_DISARMED, 16777216: SYSTEM_LEVEL, 33554432: BAD_TIMING, 67108864: UNKNOWN_PHASE_ESTIMATE, 134217728: UNKNOWN_PHASE_VEL, 268435456: UNKNOWN_TORQUE, 536870912: UNKNOWN_CURRENT_COMMAND, 1073741824: UNKNOWN_CURRENT_MEASUREMENT, 2147483648: UNKNOWN_VBUS_VOLTAGE, 4294967296: UNKNOWN_VOLTAGE_COMMAND, 8589934592: UNKNOWN_GAINS, 17179869184: CONTROLLER_INITIALIZING, 34359738368: UNBALANCED_PHASES |

### ID: 4 - Axis0_Get_Encoder_Error
- Name: Axis0_Get_Encoder_Error
- Length: 8 bytes
- Sender: ['ODrive_Axis0']

| Signal Name | Start Bit | Length | Factor | Offset | Min Value | Max Value | Unit | Receiver | Choices |
|-------------|-----------|--------|--------|--------|-----------|-----------|------|----------|---------|
| Encoder_Error | 0 | 32 | 1 | 0 | None | None |  | Master | 0: NONE, 1: UNSTABLE_GAIN, 2: CPR_POLEPAIRS_MISMATCH, 4: NO_RESPONSE, 8: UNSUPPORTED_ENCODER_MODE, 16: ILLEGAL_HALL_STATE, 32: INDEX_NOT_FOUND_YET, 64: ABS_SPI_TIMEOUT, 128: ABS_SPI_COM_FAIL, 256: ABS_SPI_NOT_READY, 512: HALL_NOT_CALIBRATED_YET |

### ID: 5 - Axis0_Get_Sensorless_Error
- Name: Axis0_Get_Sensorless_Error
- Length: 8 bytes
- Sender: ['ODrive_Axis0']

| Signal Name | Start Bit | Length | Factor | Offset | Min Value | Max Value | Unit | Receiver | Choices |
|-------------|-----------|--------|--------|--------|-----------|-----------|------|----------|---------|
| Sensorless_Error | 0 | 32 | 1 | 0 | None | None |  | Master | 0: NONE, 1: UNSTABLE_GAIN, 2: UNKNOWN_CURRENT_MEASUREMENT |

### ID: 6 - Axis0_Set_Axis_Node_ID
- Name: Axis0_Set_Axis_Node_ID
- Length: 8 bytes
- Sender: ['Master']

| Signal Name | Start Bit | Length | Factor | Offset | Min Value | Max Value | Unit | Receiver | Choices |
|-------------|-----------|--------|--------|--------|-----------|-----------|------|----------|---------|
| Axis_Node_ID | 0 | 32 | 1 | 0 | None | None |  | ODrive_Axis0 |  |

### ID: 7 - Axis0_Set_Axis_State
- Name: Axis0_Set_Axis_State
- Length: 8 bytes
- Sender: ['Master']

| Signal Name | Start Bit | Length | Factor | Offset | Min Value | Max Value | Unit | Receiver | Choices |
|-------------|-----------|--------|--------|--------|-----------|-----------|------|----------|---------|
| Axis_Requested_State | 0 | 32 | 1 | 0 | None | None |  | ODrive_Axis0 | 0: UNDEFINED, 1: IDLE, 2: STARTUP_SEQUENCE, 3: FULL_CALIBRATION_SEQUENCE, 4: MOTOR_CALIBRATION, 6: ENCODER_INDEX_SEARCH, 7: ENCODER_OFFSET_CALIBRATION, 8: CLOSED_LOOP_CONTROL, 9: LOCKIN_SPIN, 10: ENCODER_DIR_FIND, 11: HOMING, 12: ENCODER_HALL_POLARITY_CALIBRATION, 13: ENCODER_HALL_PHASE_CALIBRATION |

### ID: 9 - Axis0_Get_Encoder_Estimates
- Name: Axis0_Get_Encoder_Estimates
- Length: 8 bytes
- Sender: ['ODrive_Axis0']

| Signal Name | Start Bit | Length | Factor | Offset | Min Value | Max Value | Unit | Receiver | Choices |
|-------------|-----------|--------|--------|--------|-----------|-----------|------|----------|---------|
| Pos_Estimate | 0 | 32 | 1 | 0 | None | None | rev | Master |  |
| Vel_Estimate | 32 | 32 | 1 | 0 | None | None | rev/s | Master |  |

### ID: 10 - Axis0_Get_Encoder_Count
- Name: Axis0_Get_Encoder_Count
- Length: 8 bytes
- Sender: ['ODrive_Axis0']

| Signal Name | Start Bit | Length | Factor | Offset | Min Value | Max Value | Unit | Receiver | Choices |
|-------------|-----------|--------|--------|--------|-----------|-----------|------|----------|---------|
| Shadow_Count | 0 | 32 | 1 | 0 | None | None | counts | Master |  |
| Count_in_CPR | 32 | 32 | 1 | 0 | None | None | counts | Master |  |

### ID: 11 - Axis0_Set_Controller_Mode
- Name: Axis0_Set_Controller_Mode
- Length: 8 bytes
- Sender: ['Master']

| Signal Name | Start Bit | Length | Factor | Offset | Min Value | Max Value | Unit | Receiver | Choices |
|-------------|-----------|--------|--------|--------|-----------|-----------|------|----------|---------|
| Control_Mode | 0 | 32 | 1 | 0 | None | None |  | ODrive_Axis0 | 0: VOLTAGE_CONTROL, 1: TORQUE_CONTROL, 2: VELOCITY_CONTROL, 3: POSITION_CONTROL |
| Input_Mode | 32 | 32 | 1 | 0 | None | None |  | ODrive_Axis0 | 0: INACTIVE, 1: PASSTHROUGH, 2: VEL_RAMP, 3: POS_FILTER, 4: MIX_CHANNELS, 5: TRAP_TRAJ, 6: TORQUE_RAMP, 7: MIRROR, 8: TUNING |

### ID: 12 - Axis0_Set_Input_Pos
- Name: Axis0_Set_Input_Pos
- Length: 8 bytes
- Sender: ['Master']

| Signal Name | Start Bit | Length | Factor | Offset | Min Value | Max Value | Unit | Receiver | Choices |
|-------------|-----------|--------|--------|--------|-----------|-----------|------|----------|---------|
| Input_Pos | 0 | 32 | 1 | 0 | None | None | rev | ODrive_Axis0 |  |
| Vel_FF | 32 | 16 | 0.001 | 0 | None | None | rev/s | ODrive_Axis0 |  |
| Torque_FF | 48 | 16 | 0.001 | 0 | None | None | Nm | ODrive_Axis0 |  |

### ID: 13 - Axis0_Set_Input_Vel
- Name: Axis0_Set_Input_Vel
- Length: 8 bytes
- Sender: ['Master']

| Signal Name | Start Bit | Length | Factor | Offset | Min Value | Max Value | Unit | Receiver | Choices |
|-------------|-----------|--------|--------|--------|-----------|-----------|------|----------|---------|
| Input_Vel | 0 | 32 | 1 | 0 | None | None | rev | ODrive_Axis0 |  |
| Input_Torque_FF | 32 | 32 | 1 | 0 | None | None | rev/s | ODrive_Axis0 |  |

### ID: 14 - Axis0_Set_Input_Torque
- Name: Axis0_Set_Input_Torque
- Length: 8 bytes
- Sender: ['Master']

| Signal Name | Start Bit | Length | Factor | Offset | Min Value | Max Value | Unit | Receiver | Choices |
|-------------|-----------|--------|--------|--------|-----------|-----------|------|----------|---------|
| Input_Torque | 0 | 32 | 1 | 0 | None | None | Nm | ODrive_Axis0 |  |

### ID: 15 - Axis0_Set_Limits
- Name: Axis0_Set_Limits
- Length: 8 bytes
- Sender: ['Master']

| Signal Name | Start Bit | Length | Factor | Offset | Min Value | Max Value | Unit | Receiver | Choices |
|-------------|-----------|--------|--------|--------|-----------|-----------|------|----------|---------|
| Velocity_Limit | 0 | 32 | 1 | 0 | None | None | rev/s | ODrive_Axis0 |  |
| Current_Limit | 32 | 32 | 1 | 0 | None | None | A | ODrive_Axis0 |  |

### ID: 16 - Axis0_Start_Anticogging
- Name: Axis0_Start_Anticogging
- Length: 0 bytes
- Sender: ['Master']

| Signal Name | Start Bit | Length | Factor | Offset | Min Value | Max Value | Unit | Receiver | Choices |
|-------------|-----------|--------|--------|--------|-----------|-----------|------|----------|---------|

### ID: 17 - Axis0_Set_Traj_Vel_Limit
- Name: Axis0_Set_Traj_Vel_Limit
- Length: 8 bytes
- Sender: ['Master']

| Signal Name | Start Bit | Length | Factor | Offset | Min Value | Max Value | Unit | Receiver | Choices |
|-------------|-----------|--------|--------|--------|-----------|-----------|------|----------|---------|
| Traj_Vel_Limit | 0 | 32 | 1 | 0 | None | None | rev/s | ODrive_Axis0 |  |

### ID: 18 - Axis0_Set_Traj_Accel_Limits
- Name: Axis0_Set_Traj_Accel_Limits
- Length: 8 bytes
- Sender: ['Master']

| Signal Name | Start Bit | Length | Factor | Offset | Min Value | Max Value | Unit | Receiver | Choices |
|-------------|-----------|--------|--------|--------|-----------|-----------|------|----------|---------|
| Traj_Accel_Limit | 0 | 32 | 1 | 0 | None | None | rev/s^2 | ODrive_Axis0 |  |
| Traj_Decel_Limit | 32 | 32 | 1 | 0 | None | None | rev/s^2 | ODrive_Axis0 |  |

### ID: 19 - Axis0_Set_Traj_Inertia
- Name: Axis0_Set_Traj_Inertia
- Length: 8 bytes
- Sender: ['Master']

| Signal Name | Start Bit | Length | Factor | Offset | Min Value | Max Value | Unit | Receiver | Choices |
|-------------|-----------|--------|--------|--------|-----------|-----------|------|----------|---------|
| Traj_Inertia | 0 | 32 | 1 | 0 | None | None | Nm / (rev/s^2) | ODrive_Axis0 |  |

### ID: 20 - Axis0_Get_Iq
- Name: Axis0_Get_Iq
- Length: 8 bytes
- Sender: ['ODrive_Axis0']

| Signal Name | Start Bit | Length | Factor | Offset | Min Value | Max Value | Unit | Receiver | Choices |
|-------------|-----------|--------|--------|--------|-----------|-----------|------|----------|---------|
| Iq_Setpoint | 0 | 32 | 1 | 0 | None | None | A | Master |  |
| Iq_Measured | 32 | 32 | 1 | 0 | None | None | A | Master |  |

### ID: 21 - Axis0_Get_Sensorless_Estimates
- Name: Axis0_Get_Sensorless_Estimates
- Length: 8 bytes
- Sender: ['ODrive_Axis0']

| Signal Name | Start Bit | Length | Factor | Offset | Min Value | Max Value | Unit | Receiver | Choices |
|-------------|-----------|--------|--------|--------|-----------|-----------|------|----------|---------|
| Sensorless_Pos_Estimate | 0 | 32 | 1 | 0 | None | None | rev | Master |  |
| Sensorless_Vel_Estimate | 32 | 32 | 1 | 0 | None | None | rev/s | Master |  |

### ID: 22 - Axis0_Reboot
- Name: Axis0_Reboot
- Length: 0 bytes
- Sender: ['Master']

| Signal Name | Start Bit | Length | Factor | Offset | Min Value | Max Value | Unit | Receiver | Choices |
|-------------|-----------|--------|--------|--------|-----------|-----------|------|----------|---------|

### ID: 23 - Axis0_Get_Bus_Voltage_Current
- Name: Axis0_Get_Bus_Voltage_Current
- Length: 8 bytes
- Sender: ['ODrive_Axis0']

| Signal Name | Start Bit | Length | Factor | Offset | Min Value | Max Value | Unit | Receiver | Choices |
|-------------|-----------|--------|--------|--------|-----------|-----------|------|----------|---------|
| Bus_Voltage | 0 | 32 | 1 | 0 | None | None | V | Master |  |
| Bus_Current | 32 | 32 | 1 | 0 | None | None | A | Master |  |

### ID: 24 - Axis0_Clear_Errors
- Name: Axis0_Clear_Errors
- Length: 0 bytes
- Sender: ['Master']

| Signal Name | Start Bit | Length | Factor | Offset | Min Value | Max Value | Unit | Receiver | Choices |
|-------------|-----------|--------|--------|--------|-----------|-----------|------|----------|---------|

### ID: 25 - Axis0_Set_Linear_Count
- Name: Axis0_Set_Linear_Count
- Length: 8 bytes
- Sender: ['Master']

| Signal Name | Start Bit | Length | Factor | Offset | Min Value | Max Value | Unit | Receiver | Choices |
|-------------|-----------|--------|--------|--------|-----------|-----------|------|----------|---------|
| Position | 0 | 32 | 1 | 0 | None | None | counts | ODrive_Axis0 |  |

### ID: 26 - Axis0_Set_Pos_Gain
- Name: Axis0_Set_Pos_Gain
- Length: 8 bytes
- Sender: ['Master']

| Signal Name | Start Bit | Length | Factor | Offset | Min Value | Max Value | Unit | Receiver | Choices |
|-------------|-----------|--------|--------|--------|-----------|-----------|------|----------|---------|
| Pos_Gain | 0 | 32 | 1 | 0 | None | None | (rev/s) / rev | ODrive_Axis0 |  |

### ID: 27 - Axis0_Set_Vel_Gains
- Name: Axis0_Set_Vel_Gains
- Length: 8 bytes
- Sender: ['Master']

| Signal Name | Start Bit | Length | Factor | Offset | Min Value | Max Value | Unit | Receiver | Choices |
|-------------|-----------|--------|--------|--------|-----------|-----------|------|----------|---------|
| Vel_Gain | 0 | 32 | 1 | 0 | None | None | Nm / (rev/s) | ODrive_Axis0 |  |
| Vel_Integrator_Gain | 32 | 32 | 1 | 0 | None | None | (Nm / (rev/s)) / s | ODrive_Axis0 |  |

### ID: 28 - Axis0_Get_ADC_Voltage
- Name: Axis0_Get_ADC_Voltage
- Length: 8 bytes
- Sender: ['ODrive_Axis0']

| Signal Name | Start Bit | Length | Factor | Offset | Min Value | Max Value | Unit | Receiver | Choices |
|-------------|-----------|--------|--------|--------|-----------|-----------|------|----------|---------|
| ADC_Voltage | 0 | 32 | 1 | 0 | None | None | V | Master |  |

### ID: 29 - Axis0_Get_Controller_Error
- Name: Axis0_Get_Controller_Error
- Length: 8 bytes
- Sender: ['ODrive_Axis0']

| Signal Name | Start Bit | Length | Factor | Offset | Min Value | Max Value | Unit | Receiver | Choices |
|-------------|-----------|--------|--------|--------|-----------|-----------|------|----------|---------|
| Controller_Error | 0 | 32 | 1 | 0 | None | None |  | Master | 0: NONE, 1: OVERSPEED, 2: INVALID_INPUT_MODE, 4: UNSTABLE_GAIN, 8: INVALID_MIRROR_AXIS, 16: INVALID_LOAD_ENCODER, 32: INVALID_ESTIMATE, 64: INVALID_CIRCULAR_RANGE, 128: SPINOUT_DETECTED |

### ID: 33 - Axis1_Heartbeat
- Name: Axis1_Heartbeat
- Length: 8 bytes
- Sender: ['ODrive_Axis1']

### ID: 35 - Axis1_Get_Motor_Error
- Name: Axis1_Get_Motor_Error
- Length: 8 bytes
- Sender: ['ODrive_Axis1']

### ID: 36 - Axis1_Get_Encoder_Error
- Name: Axis1_Get_Encoder_Error
- Length: 8 bytes
- Sender: ['ODrive_Axis1']

### ID: 37 - Axis1_Get_Sensorless_Error
- Name: Axis1_Get_Sensorless_Error
- Length: 8 bytes
- Sender: ['ODrive_Axis1']

### ID: 38 - Axis1_Set_Axis_Node_ID
- Name: Axis1_Set_Axis_Node_ID
- Length: 8 bytes
- Sender: ['Master']

### ID: 39 - Axis1_Set_Axis_State
- Name: Axis1_Set_Axis_State
- Length: 8 bytes
- Sender: ['Master']

### ID: 41 - Axis1_Get_Encoder_Estimates
- Name: Axis1_Get_Encoder_Estimates
- Length: 8 bytes
- Sender: ['ODrive_Axis1']

### ID: 42 - Axis1_Get_Encoder_Count
- Name: Axis1_Get_Encoder_Count
- Length: 8 bytes
- Sender: ['ODrive_Axis1']

### ID: 43 - Axis1_Set_Controller_Mode
- Name: Axis1_Set_Controller_Mode
- Length: 8 bytes
- Sender: ['Master']

### ID: 44 - Axis1_Set_Input_Pos
- Name: Axis1_Set_Input_Pos
- Length: 8 bytes
- Sender: ['Master']

### ID: 45 - Axis1_Set_Input_Vel
- Name: Axis1_Set_Input_Vel
- Length: 8 bytes
- Sender: ['Master']

### ID: 46 - Axis1_Set_Input_Torque
- Name: Axis1_Set_Input_Torque
- Length: 8 bytes
- Sender: ['Master']

### ID: 47 - Axis1_Set_Limits
- Name: Axis1_Set_Limits
- Length: 8 bytes
- Sender: ['Master']

### ID: 48 - Axis1_Start_Anticogging
- Name: Axis1_Start_Anticogging
- Length: 0 bytes
- Sender: ['Master']

### ID: 49 - Axis1_Set_Traj_Vel_Limit
- Name: Axis1_Set_Traj_Vel_Limit
- Length: 8 bytes
- Sender: ['Master']

### ID: 50 - Axis1_Set_Traj_Accel_Limits
- Name: Axis1_Set_Traj_Accel_Limits
- Length: 8 bytes
- Sender: ['Master']

### ID: 51 - Axis1_Set_Traj_Inertia
- Name: Axis1_Set_Traj_Inertia
- Length: 8 bytes
- Sender: ['Master']

### ID: 52 - Axis1_Get_Iq
- Name: Axis1_Get_Iq
- Length: 8 bytes
- Sender: ['ODrive_Axis1']

### ID: 53 - Axis1_Get_Sensorless_Estimates
- Name: Axis1_Get_Sensorless_Estimates
- Length: 8 bytes
- Sender: ['ODrive_Axis1']

### ID: 54 - Axis1_Reboot
- Name: Axis1_Reboot
- Length: 0 bytes
- Sender: ['Master']

### ID: 55 - Axis1_Get_Bus_Voltage_Current
- Name: Axis1_Get_Bus_Voltage_Current
- Length: 8 bytes
- Sender: ['ODrive_Axis1']

### ID: 56 - Axis1_Clear_Errors
- Name: Axis1_Clear_Errors
- Length: 0 bytes
- Sender: ['Master']

### ID: 57 - Axis1_Set_Linear_Count
- Name: Axis1_Set_Linear_Count
- Length: 8 bytes
- Sender: ['Master']

### ID: 58 - Axis1_Set_Pos_Gain
- Name: Axis1_Set_Pos_Gain
- Length: 8 bytes
- Sender: ['Master']

### ID: 59 - Axis1_Set_Vel_Gains
- Name: Axis1_Set_Vel_Gains
- Length: 8 bytes
- Sender: ['Master']

### ID: 60 - Axis1_Get_ADC_Voltage
- Name: Axis1_Get_ADC_Voltage
- Length: 8 bytes
- Sender: ['ODrive_Axis1']

### ID: 61 - Axis1_Get_Controller_Error
- Name: Axis1_Get_Controller_Error
- Length: 8 bytes
- Sender: ['ODrive_Axis1']

### ID: 65 - Axis2_Heartbeat
- Name: Axis2_Heartbeat
- Length: 8 bytes
- Sender: ['ODrive_Axis2']

### ID: 67 - Axis2_Get_Motor_Error
- Name: Axis2_Get_Motor_Error
- Length: 8 bytes
- Sender: ['ODrive_Axis2']

### ID: 68 - Axis2_Get_Encoder_Error
- Name: Axis2_Get_Encoder_Error
- Length: 8 bytes
- Sender: ['ODrive_Axis2']

### ID: 69 - Axis2_Get_Sensorless_Error
- Name: Axis2_Get_Sensorless_Error
- Length: 8 bytes
- Sender: ['ODrive_Axis2']

### ID: 70 - Axis2_Set_Axis_Node_ID
- Name: Axis2_Set_Axis_Node_ID
- Length: 8 bytes
- Sender: ['Master']

### ID: 71 - Axis2_Set_Axis_State
- Name: Axis2_Set_Axis_State
- Length: 8 bytes
- Sender: ['Master']

### ID: 73 - Axis2_Get_Encoder_Estimates
- Name: Axis2_Get_Encoder_Estimates
- Length: 8 bytes
- Sender: ['ODrive_Axis2']

### ID: 74 - Axis2_Get_Encoder_Count
- Name: Axis2_Get_Encoder_Count
- Length: 8 bytes
- Sender: ['ODrive_Axis2']

### ID: 75 - Axis2_Set_Controller_Mode
- Name: Axis2_Set_Controller_Mode
- Length: 8 bytes
- Sender: ['Master']

### ID: 76 - Axis2_Set_Input_Pos
- Name: Axis2_Set_Input_Pos
- Length: 8 bytes
- Sender: ['Master']

### ID: 77 - Axis2_Set_Input_Vel
- Name: Axis2_Set_Input_Vel
- Length: 8 bytes
- Sender: ['Master']

### ID: 78 - Axis2_Set_Input_Torque
- Name: Axis2_Set_Input_Torque
- Length: 8 bytes
- Sender: ['Master']

### ID: 79 - Axis2_Set_Limits
- Name: Axis2_Set_Limits
- Length: 8 bytes
- Sender: ['Master']

### ID: 80 - Axis2_Start_Anticogging
- Name: Axis2_Start_Anticogging
- Length: 0 bytes
- Sender: ['Master']

### ID: 81 - Axis2_Set_Traj_Vel_Limit
- Name: Axis2_Set_Traj_Vel_Limit
- Length: 8 bytes
- Sender: ['Master']

### ID: 82 - Axis2_Set_Traj_Accel_Limits
- Name: Axis2_Set_Traj_Accel_Limits
- Length: 8 bytes
- Sender: ['Master']

### ID: 83 - Axis2_Set_Traj_Inertia
- Name: Axis2_Set_Traj_Inertia
- Length: 8 bytes
- Sender: ['Master']

### ID: 84 - Axis2_Get_Iq
- Name: Axis2_Get_Iq
- Length: 8 bytes
- Sender: ['ODrive_Axis2']

### ID: 85 - Axis2_Get_Sensorless_Estimates
- Name: Axis2_Get_Sensorless_Estimates
- Length: 8 bytes
- Sender: ['ODrive_Axis2']

### ID: 86 - Axis2_Reboot
- Name: Axis2_Reboot
- Length: 0 bytes
- Sender: ['Master']

### ID: 87 - Axis2_Get_Bus_Voltage_Current
- Name: Axis2_Get_Bus_Voltage_Current
- Length: 8 bytes
- Sender: ['ODrive_Axis2']

### ID: 88 - Axis2_Clear_Errors
- Name: Axis2_Clear_Errors
- Length: 0 bytes
- Sender: ['Master']

### ID: 89 - Axis2_Set_Linear_Count
- Name: Axis2_Set_Linear_Count
- Length: 8 bytes
- Sender: ['Master']

### ID: 90 - Axis2_Set_Pos_Gain
- Name: Axis2_Set_Pos_Gain
- Length: 8 bytes
- Sender: ['Master']

### ID: 91 - Axis2_Set_Vel_Gains
- Name: Axis2_Set_Vel_Gains
- Length: 8 bytes
- Sender: ['Master']

### ID: 92 - Axis2_Get_ADC_Voltage
- Name: Axis2_Get_ADC_Voltage
- Length: 8 bytes
- Sender: ['ODrive_Axis2']

### ID: 93 - Axis2_Get_Controller_Error
- Name: Axis2_Get_Controller_Error
- Length: 8 bytes
- Sender: ['ODrive_Axis2']

### ID: 97 - Axis3_Heartbeat
- Name: Axis3_Heartbeat
- Length: 8 bytes
- Sender: ['ODrive_Axis3']

### ID: 99 - Axis3_Get_Motor_Error
- Name: Axis3_Get_Motor_Error
- Length: 8 bytes
- Sender: ['ODrive_Axis3']

### ID: 100 - Axis3_Get_Encoder_Error
- Name: Axis3_Get_Encoder_Error
- Length: 8 bytes
- Sender: ['ODrive_Axis3']

### ID: 101 - Axis3_Get_Sensorless_Error
- Name: Axis3_Get_Sensorless_Error
- Length: 8 bytes
- Sender: ['ODrive_Axis3']

### ID: 102 - Axis3_Set_Axis_Node_ID
- Name: Axis3_Set_Axis_Node_ID
- Length: 8 bytes
- Sender: ['Master']

### ID: 103 - Axis3_Set_Axis_State
- Name: Axis3_Set_Axis_State
- Length: 8 bytes
- Sender: ['Master']

### ID: 105 - Axis3_Get_Encoder_Estimates
- Name: Axis3_Get_Encoder_Estimates
- Length: 8 bytes
- Sender: ['ODrive_Axis3']

### ID: 106 - Axis3_Get_Encoder_Count
- Name: Axis3_Get_Encoder_Count
- Length: 8 bytes
- Sender: ['ODrive_Axis3']

### ID: 107 - Axis3_Set_Controller_Mode
- Name: Axis3_Set_Controller_Mode
- Length: 8 bytes
- Sender: ['Master']

### ID: 108 - Axis3_Set_Input_Pos
- Name: Axis3_Set_Input_Pos
- Length: 8 bytes
- Sender: ['Master']

### ID: 109 - Axis3_Set_Input_Vel
- Name: Axis3_Set_Input_Vel
- Length: 8 bytes
- Sender: ['Master']

### ID: 110 - Axis3_Set_Input_Torque
- Name: Axis3_Set_Input_Torque
- Length: 8 bytes
- Sender: ['Master']

### ID: 111 - Axis3_Set_Limits
- Name: Axis3_Set_Limits
- Length: 8 bytes
- Sender: ['Master']

### ID: 112 - Axis3_Start_Anticogging
- Name: Axis3_Start_Anticogging
- Length: 0 bytes
- Sender: ['Master']

### ID: 113 - Axis3_Set_Traj_Vel_Limit
- Name: Axis3_Set_Traj_Vel_Limit
- Length: 8 bytes
- Sender: ['Master']

### ID: 114 - Axis3_Set_Traj_Accel_Limits
- Name: Axis3_Set_Traj_Accel_Limits
- Length: 8 bytes
- Sender: ['Master']

### ID: 115 - Axis3_Set_Traj_Inertia
- Name: Axis3_Set_Traj_Inertia
- Length: 8 bytes
- Sender: ['Master']

### ID: 116 - Axis3_Get_Iq
- Name: Axis3_Get_Iq
- Length: 8 bytes
- Sender: ['ODrive_Axis3']

### ID: 117 - Axis3_Get_Sensorless_Estimates
- Name: Axis3_Get_Sensorless_Estimates
- Length: 8 bytes
- Sender: ['ODrive_Axis3']

### ID: 118 - Axis3_Reboot
- Name: Axis3_Reboot
- Length: 0 bytes
- Sender: ['Master']

### ID: 119 - Axis3_Get_Bus_Voltage_Current
- Name: Axis3_Get_Bus_Voltage_Current
- Length: 8 bytes
- Sender: ['ODrive_Axis3']

### ID: 120 - Axis3_Clear_Errors
- Name: Axis3_Clear_Errors
- Length: 0 bytes
- Sender: ['Master']

### ID: 121 - Axis3_Set_Linear_Count
- Name: Axis3_Set_Linear_Count
- Length: 8 bytes
- Sender: ['Master']

### ID: 122 - Axis3_Set_Pos_Gain
- Name: Axis3_Set_Pos_Gain
- Length: 8 bytes
- Sender: ['Master']

### ID: 123 - Axis3_Set_Vel_Gains
- Name: Axis3_Set_Vel_Gains
- Length: 8 bytes
- Sender: ['Master']

### ID: 124 - Axis3_Get_ADC_Voltage
- Name: Axis3_Get_ADC_Voltage
- Length: 8 bytes
- Sender: ['ODrive_Axis3']

### ID: 125 - Axis3_Get_Controller_Error
- Name: Axis3_Get_Controller_Error
- Length: 8 bytes
- Sender: ['ODrive_Axis3']

### ID: 129 - Axis4_Heartbeat
- Name: Axis4_Heartbeat
- Length: 8 bytes
- Sender: ['ODrive_Axis4']

### ID: 131 - Axis4_Get_Motor_Error
- Name: Axis4_Get_Motor_Error
- Length: 8 bytes
- Sender: ['ODrive_Axis4']

### ID: 132 - Axis4_Get_Encoder_Error
- Name: Axis4_Get_Encoder_Error
- Length: 8 bytes
- Sender: ['ODrive_Axis4']

### ID: 133 - Axis4_Get_Sensorless_Error
- Name: Axis4_Get_Sensorless_Error
- Length: 8 bytes
- Sender: ['ODrive_Axis4']

### ID: 134 - Axis4_Set_Axis_Node_ID
- Name: Axis4_Set_Axis_Node_ID
- Length: 8 bytes
- Sender: ['Master']

### ID: 135 - Axis4_Set_Axis_State
- Name: Axis4_Set_Axis_State
- Length: 8 bytes
- Sender: ['Master']

### ID: 137 - Axis4_Get_Encoder_Estimates
- Name: Axis4_Get_Encoder_Estimates
- Length: 8 bytes
- Sender: ['ODrive_Axis4']

### ID: 138 - Axis4_Get_Encoder_Count
- Name: Axis4_Get_Encoder_Count
- Length: 8 bytes
- Sender: ['ODrive_Axis4']

### ID: 139 - Axis4_Set_Controller_Mode
- Name: Axis4_Set_Controller_Mode
- Length: 8 bytes
- Sender: ['Master']

### ID: 140 - Axis4_Set_Input_Pos
- Name: Axis4_Set_Input_Pos
- Length: 8 bytes
- Sender: ['Master']

### ID: 141 - Axis4_Set_Input_Vel
- Name: Axis4_Set_Input_Vel
- Length: 8 bytes
- Sender: ['Master']

### ID: 142 - Axis4_Set_Input_Torque
- Name: Axis4_Set_Input_Torque
- Length: 8 bytes
- Sender: ['Master']

### ID: 143 - Axis4_Set_Limits
- Name: Axis4_Set_Limits
- Length: 8 bytes
- Sender: ['Master']

### ID: 144 - Axis4_Start_Anticogging
- Name: Axis4_Start_Anticogging
- Length: 0 bytes
- Sender: ['Master']

### ID: 145 - Axis4_Set_Traj_Vel_Limit
- Name: Axis4_Set_Traj_Vel_Limit
- Length: 8 bytes
- Sender: ['Master']

### ID: 146 - Axis4_Set_Traj_Accel_Limits
- Name: Axis4_Set_Traj_Accel_Limits
- Length: 8 bytes
- Sender: ['Master']

### ID: 147 - Axis4_Set_Traj_Inertia
- Name: Axis4_Set_Traj_Inertia
- Length: 8 bytes
- Sender: ['Master']

### ID: 148 - Axis4_Get_Iq
- Name: Axis4_Get_Iq
- Length: 8 bytes
- Sender: ['ODrive_Axis4']

### ID: 149 - Axis4_Get_Sensorless_Estimates
- Name: Axis4_Get_Sensorless_Estimates
- Length: 8 bytes
- Sender: ['ODrive_Axis4']

### ID: 150 - Axis4_Reboot
- Name: Axis4_Reboot
- Length: 0 bytes
- Sender: ['Master']

### ID: 151 - Axis4_Get_Bus_Voltage_Current
- Name: Axis4_Get_Bus_Voltage_Current
- Length: 8 bytes
- Sender: ['ODrive_Axis4']

### ID: 152 - Axis4_Clear_Errors
- Name: Axis4_Clear_Errors
- Length: 0 bytes
- Sender: ['Master']

### ID: 153 - Axis4_Set_Linear_Count
- Name: Axis4_Set_Linear_Count
- Length: 8 bytes
- Sender: ['Master']

### ID: 154 - Axis4_Set_Pos_Gain
- Name: Axis4_Set_Pos_Gain
- Length: 8 bytes
- Sender: ['Master']

### ID: 155 - Axis4_Set_Vel_Gains
- Name: Axis4_Set_Vel_Gains
- Length: 8 bytes
- Sender: ['Master']

### ID: 156 - Axis4_Get_ADC_Voltage
- Name: Axis4_Get_ADC_Voltage
- Length: 8 bytes
- Sender: ['ODrive_Axis4']

### ID: 157 - Axis4_Get_Controller_Error
- Name: Axis4_Get_Controller_Error
- Length: 8 bytes
- Sender: ['ODrive_Axis4']

### ID: 161 - Axis5_Heartbeat
- Name: Axis5_Heartbeat
- Length: 8 bytes
- Sender: ['ODrive_Axis5']

### ID: 163 - Axis5_Get_Motor_Error
- Name: Axis5_Get_Motor_Error
- Length: 8 bytes
- Sender: ['ODrive_Axis5']

### ID: 164 - Axis5_Get_Encoder_Error
- Name: Axis5_Get_Encoder_Error
- Length: 8 bytes
- Sender: ['ODrive_Axis5']

### ID: 165 - Axis5_Get_Sensorless_Error
- Name: Axis5_Get_Sensorless_Error
- Length: 8 bytes
- Sender: ['ODrive_Axis5']

### ID: 166 - Axis5_Set_Axis_Node_ID
- Name: Axis5_Set_Axis_Node_ID
- Length: 8 bytes
- Sender: ['Master']

### ID: 167 - Axis5_Set_Axis_State
- Name: Axis5_Set_Axis_State
- Length: 8 bytes
- Sender: ['Master']

### ID: 169 - Axis5_Get_Encoder_Estimates
- Name: Axis5_Get_Encoder_Estimates
- Length: 8 bytes
- Sender: ['ODrive_Axis5']

### ID: 170 - Axis5_Get_Encoder_Count
- Name: Axis5_Get_Encoder_Count
- Length: 8 bytes
- Sender: ['ODrive_Axis5']

### ID: 171 - Axis5_Set_Controller_Mode
- Name: Axis5_Set_Controller_Mode
- Length: 8 bytes
- Sender: ['Master']

### ID: 172 - Axis5_Set_Input_Pos
- Name: Axis5_Set_Input_Pos
- Length: 8 bytes
- Sender: ['Master']

### ID: 173 - Axis5_Set_Input_Vel
- Name: Axis5_Set_Input_Vel
- Length: 8 bytes
- Sender: ['Master']

### ID: 174 - Axis5_Set_Input_Torque
- Name: Axis5_Set_Input_Torque
- Length: 8 bytes
- Sender: ['Master']

### ID: 175 - Axis5_Set_Limits
- Name: Axis5_Set_Limits
- Length: 8 bytes
- Sender: ['Master']

### ID: 176 - Axis5_Start_Anticogging
- Name: Axis5_Start_Anticogging
- Length: 0 bytes
- Sender: ['Master']

### ID: 177 - Axis5_Set_Traj_Vel_Limit
- Name: Axis5_Set_Traj_Vel_Limit
- Length: 8 bytes
- Sender: ['Master']

### ID: 178 - Axis5_Set_Traj_Accel_Limits
- Name: Axis5_Set_Traj_Accel_Limits
- Length: 8 bytes
- Sender: ['Master']

### ID: 179 - Axis5_Set_Traj_Inertia
- Name: Axis5_Set_Traj_Inertia
- Length: 8 bytes
- Sender: ['Master']

### ID: 180 - Axis5_Get_Iq
- Name: Axis5_Get_Iq
- Length: 8 bytes
- Sender: ['ODrive_Axis5']

### ID: 181 - Axis5_Get_Sensorless_Estimates
- Name: Axis5_Get_Sensorless_Estimates
- Length: 8 bytes
- Sender: ['ODrive_Axis5']

### ID: 182 - Axis5_Reboot
- Name: Axis5_Reboot
- Length: 0 bytes
- Sender: ['Master']

### ID: 183 - Axis5_Get_Bus_Voltage_Current
- Name: Axis5_Get_Bus_Voltage_Current
- Length: 8 bytes
- Sender: ['ODrive_Axis5']

### ID: 184 - Axis5_Clear_Errors
- Name: Axis5_Clear_Errors
- Length: 0 bytes
- Sender: ['Master']

### ID: 185 - Axis5_Set_Linear_Count
- Name: Axis5_Set_Linear_Count
- Length: 8 bytes
- Sender: ['Master']

### ID: 186 - Axis5_Set_Pos_Gain
- Name: Axis5_Set_Pos_Gain
- Length: 8 bytes
- Sender: ['Master']

### ID: 187 - Axis5_Set_Vel_Gains
- Name: Axis5_Set_Vel_Gains
- Length: 8 bytes
- Sender: ['Master']

### ID: 188 - Axis5_Get_ADC_Voltage
- Name: Axis5_Get_ADC_Voltage
- Length: 8 bytes
- Sender: ['ODrive_Axis5']

### ID: 189 - Axis5_Get_Controller_Error
- Name: Axis5_Get_Controller_Error
- Length: 8 bytes
- Sender: ['ODrive_Axis5']

### ID: 193 - Axis6_Heartbeat
- Name: Axis6_Heartbeat
- Length: 8 bytes
- Sender: ['ODrive_Axis6']

### ID: 195 - Axis6_Get_Motor_Error
- Name: Axis6_Get_Motor_Error
- Length: 8 bytes
- Sender: ['ODrive_Axis6']

### ID: 196 - Axis6_Get_Encoder_Error
- Name: Axis6_Get_Encoder_Error
- Length: 8 bytes
- Sender: ['ODrive_Axis6']

### ID: 197 - Axis6_Get_Sensorless_Error
- Name: Axis6_Get_Sensorless_Error
- Length: 8 bytes
- Sender: ['ODrive_Axis6']

### ID: 198 - Axis6_Set_Axis_Node_ID
- Name: Axis6_Set_Axis_Node_ID
- Length: 8 bytes
- Sender: ['Master']

### ID: 199 - Axis6_Set_Axis_State
- Name: Axis6_Set_Axis_State
- Length: 8 bytes
- Sender: ['Master']

### ID: 201 - Axis6_Get_Encoder_Estimates
- Name: Axis6_Get_Encoder_Estimates
- Length: 8 bytes
- Sender: ['ODrive_Axis6']

### ID: 202 - Axis6_Get_Encoder_Count
- Name: Axis6_Get_Encoder_Count
- Length: 8 bytes
- Sender: ['ODrive_Axis6']

### ID: 203 - Axis6_Set_Controller_Mode
- Name: Axis6_Set_Controller_Mode
- Length: 8 bytes
- Sender: ['Master']

### ID: 204 - Axis6_Set_Input_Pos
- Name: Axis6_Set_Input_Pos
- Length: 8 bytes
- Sender: ['Master']

### ID: 205 - Axis6_Set_Input_Vel
- Name: Axis6_Set_Input_Vel
- Length: 8 bytes
- Sender: ['Master']

### ID: 206 - Axis6_Set_Input_Torque
- Name: Axis6_Set_Input_Torque
- Length: 8 bytes
- Sender: ['Master']

### ID: 207 - Axis6_Set_Limits
- Name: Axis6_Set_Limits
- Length: 8 bytes
- Sender: ['Master']

### ID: 208 - Axis6_Start_Anticogging
- Name: Axis6_Start_Anticogging
- Length: 0 bytes
- Sender: ['Master']

### ID: 209 - Axis6_Set_Traj_Vel_Limit
- Name: Axis6_Set_Traj_Vel_Limit
- Length: 8 bytes
- Sender: ['Master']

### ID: 210 - Axis6_Set_Traj_Accel_Limits
- Name: Axis6_Set_Traj_Accel_Limits
- Length: 8 bytes
- Sender: ['Master']

### ID: 211 - Axis6_Set_Traj_Inertia
- Name: Axis6_Set_Traj_Inertia
- Length: 8 bytes
- Sender: ['Master']

### ID: 212 - Axis6_Get_Iq
- Name: Axis6_Get_Iq
- Length: 8 bytes
- Sender: ['ODrive_Axis6']

### ID: 213 - Axis6_Get_Sensorless_Estimates
- Name: Axis6_Get_Sensorless_Estimates
- Length: 8 bytes
- Sender: ['ODrive_Axis6']

### ID: 214 - Axis6_Reboot
- Name: Axis6_Reboot
- Length: 0 bytes
- Sender: ['Master']

### ID: 215 - Axis6_Get_Bus_Voltage_Current
- Name: Axis6_Get_Bus_Voltage_Current
- Length: 8 bytes
- Sender: ['ODrive_Axis6']

### ID: 216 - Axis6_Clear_Errors
- Name: Axis6_Clear_Errors
- Length: 0 bytes
- Sender: ['Master']

### ID: 217 - Axis6_Set_Linear_Count
- Name: Axis6_Set_Linear_Count
- Length: 8 bytes
- Sender: ['Master']

### ID: 218 - Axis6_Set_Pos_Gain
- Name: Axis6_Set_Pos_Gain
- Length: 8 bytes
- Sender: ['Master']

### ID: 219 - Axis6_Set_Vel_Gains
- Name: Axis6_Set_Vel_Gains
- Length: 8 bytes
- Sender: ['Master']

### ID: 220 - Axis6_Get_ADC_Voltage
- Name: Axis6_Get_ADC_Voltage
- Length: 8 bytes
- Sender: ['ODrive_Axis6']

### ID: 221 - Axis6_Get_Controller_Error
- Name: Axis6_Get_Controller_Error
- Length: 8 bytes
- Sender: ['ODrive_Axis6']

### ID: 225 - Axis7_Heartbeat
- Name: Axis7_Heartbeat
- Length: 8 bytes
- Sender: ['ODrive_Axis7']

### ID: 227 - Axis7_Get_Motor_Error
- Name: Axis7_Get_Motor_Error
- Length: 8 bytes
- Sender: ['ODrive_Axis7']

### ID: 228 - Axis7_Get_Encoder_Error
- Name: Axis7_Get_Encoder_Error
- Length: 8 bytes
- Sender: ['ODrive_Axis7']

### ID: 229 - Axis7_Get_Sensorless_Error
- Name: Axis7_Get_Sensorless_Error
- Length: 8 bytes
- Sender: ['ODrive_Axis7']

### ID: 230 - Axis7_Set_Axis_Node_ID
- Name: Axis7_Set_Axis_Node_ID
- Length: 8 bytes
- Sender: ['Master']

### ID: 231 - Axis7_Set_Axis_State
- Name: Axis7_Set_Axis_State
- Length: 8 bytes
- Sender: ['Master']

### ID: 233 - Axis7_Get_Encoder_Estimates
- Name: Axis7_Get_Encoder_Estimates
- Length: 8 bytes
- Sender: ['ODrive_Axis7']

### ID: 234 - Axis7_Get_Encoder_Count
- Name: Axis7_Get_Encoder_Count
- Length: 8 bytes
- Sender: ['ODrive_Axis7']

### ID: 235 - Axis7_Set_Controller_Mode
- Name: Axis7_Set_Controller_Mode
- Length: 8 bytes
- Sender: ['Master']

### ID: 236 - Axis7_Set_Input_Pos
- Name: Axis7_Set_Input_Pos
- Length: 8 bytes
- Sender: ['Master']

### ID: 237 - Axis7_Set_Input_Vel
- Name: Axis7_Set_Input_Vel
- Length: 8 bytes
- Sender: ['Master']

### ID: 238 - Axis7_Set_Input_Torque
- Name: Axis7_Set_Input_Torque
- Length: 8 bytes
- Sender: ['Master']

### ID: 239 - Axis7_Set_Limits
- Name: Axis7_Set_Limits
- Length: 8 bytes
- Sender: ['Master']

### ID: 240 - Axis7_Start_Anticogging
- Name: Axis7_Start_Anticogging
- Length: 0 bytes
- Sender: ['Master']

### ID: 241 - Axis7_Set_Traj_Vel_Limit
- Name: Axis7_Set_Traj_Vel_Limit
- Length: 8 bytes
- Sender: ['Master']

### ID: 242 - Axis7_Set_Traj_Accel_Limits
- Name: Axis7_Set_Traj_Accel_Limits
- Length: 8 bytes
- Sender: ['Master']

### ID: 243 - Axis7_Set_Traj_Inertia
- Name: Axis7_Set_Traj_Inertia
- Length: 8 bytes
- Sender: ['Master']

### ID: 244 - Axis7_Get_Iq
- Name: Axis7_Get_Iq
- Length: 8 bytes
- Sender: ['ODrive_Axis7']

### ID: 245 - Axis7_Get_Sensorless_Estimates
- Name: Axis7_Get_Sensorless_Estimates
- Length: 8 bytes
- Sender: ['ODrive_Axis7']

### ID: 246 - Axis7_Reboot
- Name: Axis7_Reboot
- Length: 0 bytes
- Sender: ['Master']

### ID: 247 - Axis7_Get_Bus_Voltage_Current
- Name: Axis7_Get_Bus_Voltage_Current
- Length: 8 bytes
- Sender: ['ODrive_Axis7']

### ID: 248 - Axis7_Clear_Errors
- Name: Axis7_Clear_Errors
- Length: 0 bytes
- Sender: ['Master']

### ID: 249 - Axis7_Set_Linear_Count
- Name: Axis7_Set_Linear_Count
- Length: 8 bytes
- Sender: ['Master']

### ID: 250 - Axis7_Set_Pos_Gain
- Name: Axis7_Set_Pos_Gain
- Length: 8 bytes
- Sender: ['Master']

### ID: 251 - Axis7_Set_Vel_Gains
- Name: Axis7_Set_Vel_Gains
- Length: 8 bytes
- Sender: ['Master']

### ID: 252 - Axis7_Get_ADC_Voltage
- Name: Axis7_Get_ADC_Voltage
- Length: 8 bytes
- Sender: ['ODrive_Axis7']

### ID: 253 - Axis7_Get_Controller_Error
- Name: Axis7_Get_Controller_Error
- Length: 8 bytes
- Sender: ['ODrive_Axis7']


# Odrive cansimple interface


See also original odrive docs:

* [can guide](https://docs.odriverobotics.com/v/0.5.6/can-guide.html)
* [cansimple protocol](https://docs.odriverobotics.com/v/0.5.6/can-protocol.html#can-protocol)


```python

--8<-- "examples/can_messages.py"

```

output:


    Message: message('Axis0_Heartbeat', 0x1, False, 8, None)
    Encoded: b'\x01\x00\x00\x00\x0b\x00\x00\x00'
    Decoded: {'Axis_Error': 'INVALID_STATE', 'Axis_State': 'HOMING', 'Motor_Error_Flag': 0, 'Encoder_Error_Flag': 0, 'Controller_Error_Flag': 0, 'Trajectory_Done_Flag': 0}


---------------------------------------
generated from dbc file by `scripts/gen_dbc_docs.py`

--8<-- "scripts/odrive-cansimple-0.5.6.md"



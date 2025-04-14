# Example on how to use the DBC file to encode and decode messages
import can
from odrive_can import get_dbc
from odrive_can.odrive import CanMsg

db = get_dbc()  # load default DBC

# get message
db_msg = db.get_message_by_name("Axis0_Heartbeat")
print("Message:", db_msg)

# Both numeric and string values are accepted, choices are converted to integers
data = db_msg.encode(
    {
        "Axis_Error": "NONE",
        "Axis_State": 11,
        "Motor_Error_Flag": 0,
        "Encoder_Error_Flag": 0,
        "Controller_Error_Flag": 0,
        "Trajectory_Done_Flag": 0,
    }
)
print("Data:", data)

# decode message to dict
data_dict = db_msg.decode(data)
print("Decoded:", data_dict)
print("Frame ID:", db_msg.frame_id)

# get numeric value for "Axis_Error"
axis_error_value = data_dict["Axis_Error"]


# create CanMsg
msg = can.Message(arbitration_id=db_msg.frame_id, data=data)
print(f"{msg=}")

can_msg = CanMsg(msg)
print(f"{can_msg=}")

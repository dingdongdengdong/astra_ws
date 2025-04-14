from odrive_can import get_dbc, extract_ids


def test_get_db():
    """check database loading"""

    _ = get_dbc()


def test_message_ids():
    dbc = get_dbc()
    for axis_id in range(7):
        dbc_msg = dbc.get_message_by_name(f"Axis{axis_id}_Heartbeat")

        # heartbeat message 0x01
        can_id = axis_id << 5 | 0x01
        assert dbc_msg.frame_id == can_id
        ids = extract_ids(can_id)
        assert ids == (axis_id, 0x01)

        # motor error  0x03
        dbc_msg = dbc.get_message_by_name(f"Axis{axis_id}_Get_Motor_Error")
        can_id = axis_id << 5 | 0x03
        assert dbc_msg.frame_id == can_id
        ids = extract_ids(can_id)
        assert ids == (axis_id, 0x03)

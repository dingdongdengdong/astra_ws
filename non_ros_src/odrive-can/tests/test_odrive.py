import can
import pytest

from odrive_can.odrive import CanMsg, DriveError, HeartbeatError, ODriveCAN, dbc

# pylint: disable=redefined-outer-name, protected-access


# Mocking the dbc.get_message_by_frame_id and dbc.get_message_by_name methods
@pytest.fixture(autouse=True)
def mock_dbc_methods(mocker):
    mocker.patch.object(dbc, "get_message_by_frame_id", autospec=True)
    mocker.patch.object(dbc, "get_message_by_name", autospec=True)
    # Add any necessary logic for the mocked methods if needed


@pytest.fixture
def mock_can_message():
    return can.Message(arbitration_id=123, data=[0, 1, 2, 3, 4, 5, 6, 7])


@pytest.fixture
def odrive_can(mocker):
    mocker.patch("odrive_can.odrive.can.interface.Bus")
    return ODriveCAN(axis_id=0, interface="can0", interface_type="socketcan")


def test_can_msg_init(mock_can_message):
    can_msg = CanMsg(mock_can_message)
    assert can_msg.name  # Add more specific assertions based on your dbc parsing logic
    _ = str(can_msg)  # Test __str__ method


def test_check_alive_no_heartbeat(odrive_can):
    with pytest.raises(HeartbeatError):
        odrive_can.check_alive()


def test_check_alive_with_heartbeat(odrive_can, mock_can_message):
    # Mocking a heartbeat message
    mock_can_message.arbitration_id = 1  # Arbitration ID for heartbeat
    can_msg = CanMsg(mock_can_message)
    odrive_can._last_heartbeat = can_msg

    try:
        odrive_can.check_alive()
    except HeartbeatError:
        pytest.fail("HeartbeatError raised unexpectedly")


# test check errors
def test_check_errors_no_errors(odrive_can, mock_can_message):
    mock_can_message.arbitration_id = 1  # Arbitration ID for heartbeat
    heartbeat_msg = CanMsg(mock_can_message)
    heartbeat_msg.data = {
        "Axis_Error": "NONE",
        "Motor_Error_Flag": 0,
        "Encoder_Error_Flag": 0,
        "Controller_Error_Flag": 0,
    }
    odrive_can._last_heartbeat = heartbeat_msg

    try:
        odrive_can.check_errors()
    except DriveError:
        pytest.fail("DriveError raised unexpectedly")


def test_check_errors_with_errors(odrive_can, mock_can_message):
    mock_can_message.arbitration_id = 1  # Arbitration ID for heartbeat
    heartbeat_msg = CanMsg(mock_can_message)
    heartbeat_msg.data = {
        "Axis_Error": "ERROR",
        "Motor_Error_Flag": 1,
        "Encoder_Error_Flag": 0,
        "Controller_Error_Flag": 0,
    }
    odrive_can._last_heartbeat = heartbeat_msg

    with pytest.raises(DriveError):
        odrive_can.check_errors()

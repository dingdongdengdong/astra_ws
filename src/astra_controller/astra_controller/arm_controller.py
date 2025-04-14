import serial
import threading
import numpy as np
import struct
import math
import time
import sys
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class ArmController:
    # Communication packet constants
    COMM_LEN = 2 + 16 + 1  # Total packet length: 2 bytes header/type + 16 bytes data + 1 byte checksum
    COMM_HEAD = 0x5A  # Header byte to mark the start of a packet
    COMM_TYPE_PING = 0x00  # Packet type for ping request
    COMM_TYPE_PONG = 0x01  # Packet type for pong response
    COMM_TYPE_CTRL = 0x02  # Packet type for control commands (e.g., set position)
    COMM_TYPE_FEEDBACK = 0x03  # Packet type for arm feedback (position data)
    COMM_TYPE_TORQUE = 0x04  # Packet type for torque enable/disable
    COMM_TYPE_CONFIG_WRITE = 0x05  # Packet type for writing configuration
    COMM_TYPE_CONFIG_READ = 0x06  # Packet type for reading configuration
    COMM_TYPE_CONFIG_FEEDBACK = 0x07  # Packet type for configuration feedback
    COMM_TYPE_PIDTUNE = 0x08  # Packet type for tuning PID parameters
    COMM_TYPE_INIT_JOINT = 0x09  # Packet type for initializing joint positions

    GRIPPER_GEAR_R = 0.027 / 2  # Gripper gear radius in meters (0.0135m)

    @staticmethod
    def to_si_unit(arr):
        # Convert raw sensor values to SI units (radians for joints, meters for gripper)
        arr = arr.copy()  # Create a copy to avoid modifying the input
        arr = -(np.array(arr) - 2048) / 4096 * (2 * math.pi)  # Convert joints 0-4 to radians from raw (12-bit encoder: 0-4095)
        arr[-1] *= ArmController.GRIPPER_GEAR_R  # Convert gripper raw value to meters (linear motion)
        arr[-1] += 0.03  # Add offset so 0.03m (30mm) is the open position of the gripper
        return arr

    @staticmethod
    def to_raw_unit(arr):
        # Convert SI units back to raw sensor values
        arr = arr.copy()  # Create a copy to avoid modifying the input
        arr[-1] -= 0.03  # Remove gripper offset (30mm when open)
        arr[-1] /= ArmController.GRIPPER_GEAR_R  # Convert gripper from meters to raw units
        arr = (-np.array(arr) / (2 * math.pi) * 4096 + 2048).astype(int)  # Convert radians to raw (12-bit encoder)
        return arr

    def __init__(self, name):
        # Initialize the ArmController with a serial device name (e.g., '/dev/ttyUSB0')
        logger.info(f"Using device {name}")
        self.state_cb = None  # Callback for state updates (position, velocity, effort)
        self.pong_cb = None  # Callback for pong responses
        self.ser = serial.Serial(name, 921600, timeout=None)  # Open serial port at 921600 baud
        self.lock = threading.Lock()  # Thread lock for safe access to shared state
        self.last_position = None  # Last known position (SI units)
        self.last_velocity = None  # Last known velocity (SI units/time)
        self.last_effort = None  # Last known effort (acceleration-like)
        self.last_time = None  # Timestamp of last update
        self.write_lock = threading.Lock()  # Lock for serial writes
        self.config_cb = None  # Callback for configuration feedback
        self.config_cb_lock = threading.Lock()  # Lock for config callback
        self.debug_cb = None  # Callback for debug data
        self.error_cb = None  # Callback for error reporting
        self.quit = threading.Event()  # Event to signal thread termination
        self.t = threading.Thread(target=self.recv_thread, daemon=True)  # Daemon thread for receiving data
        self.t.start()  # Start the receive thread
        self.set_torque(1)  # Enable torque on startup
        self.set_pid()  # Set default PID parameters
        while self.last_position is None:  # Wait for initial feedback
            time.sleep(0.1)

    def set_pid(self, p=30, i=0, d=0, i_max=800, p2=10, p2_err_thres=2, i_clip_thres=100000.0, i_clip_coef=1):
        # Set PID parameters for arm control
        # p: Proportional gain, i: Integral gain, d: Derivative gain
        # i_max: Max integral value, p2: Secondary proportional gain, p2_err_thres: Error threshold for p2
        # i_clip_thres: Threshold to clip integral, i_clip_coef: Coefficient for clipping
        self.write(struct.pack('>BBffffffff', self.COMM_HEAD, self.COMM_TYPE_PIDTUNE, p, i, d, i_clip_thres, i_clip_coef, i_max, p2, p2_err_thres))

    @staticmethod
    def checksum(data: bytes):
        # Verify packet checksum (sum of bytes 1 to -2 mod 256 equals last byte)
        checksum = 0
        for b in data[1:-1]:
            checksum = (checksum + b) % 256
        return checksum == data[-1]

    databuf = bytearray()  # Buffer for debug data outside standard packets

    def recv_thread(self):
        # Background thread to continuously receive and process serial data
        try:
            while not self.quit.is_set():
                data = self.ser.read(1)  # Read one byte
                if data[0] != self.COMM_HEAD:  # If not a packet header
                    if data[0] in [b'\n'[0], b'\r'[0]]:  # Check for newline or carriage return
                        if len(self.databuf) > 0 and all(c in b'0123456789-., ' for c in self.databuf):
                            try:
                                debugdata = [float(x) for x in self.databuf.decode("ascii").split(",")]  # Parse debug data
                                if self.debug_cb:
                                    self.debug_cb(debugdata)  # Call debug callback
                            except:
                                pass
                        self.databuf = bytearray()  # Reset buffer
                    else:
                        self.databuf.extend(data)  # Append to debug buffer
                    sys.stdout.buffer.write(data)  # Echo to stdout
                    sys.stdout.flush()
                    continue

                data += self.ser.read(self.COMM_LEN - 1)  # Read rest of packet
                if len(data) != self.COMM_LEN:  # Verify packet length
                    continue

                if not self.checksum(data):  # Check packet integrity
                    logger.error(f"Checksum failed: {data.hex()}")
                    continue

                if data[1] == self.COMM_TYPE_PONG:  # Handle pong response
                    if self.pong_cb:
                        self.pong_cb(struct.unpack('>HHHHHHxxxx', data[2:-1]))  # Unpack 6 uint16 values
                elif data[1] == self.COMM_TYPE_FEEDBACK:  # Handle position feedback
                    position = self.to_si_unit(struct.unpack('>HHHHHHxxxx', data[2:-1]))  # Convert raw to SI
                    this_time = time.time()  # Current timestamp
                    with self.lock:  # Thread-safe update
                        if self.last_time is None:  # First update
                            self.last_position = position
                            self.last_velocity = np.zeros(6)  # Initial velocity is zero
                            self.last_effort = np.zeros(6)  # Initial effort is zero
                            self.last_time = this_time - 1  # Avoid division by zero
                        else:
                            delta_time = this_time - self.last_time  # Time difference
                            velocity = (position - self.last_position) / delta_time  # Calculate velocity
                            effort = (velocity - self.last_velocity) / delta_time  # Calculate effort (derivative)
                            self.last_position = position
                            self.last_velocity = velocity
                            self.last_effort = effort
                            self.last_time = this_time
                        if self.state_cb:
                            self.state_cb(self.last_position, self.last_velocity, self.last_effort, self.last_time)  # Call state callback
                elif data[1] == self.COMM_TYPE_CONFIG_FEEDBACK:  # Handle config feedback
                    if self.config_cb:
                        self.config_cb(data[2:-1])  # Pass raw data to callback
        finally:
            logger.info("Receive thread exiting")

    def get_pos(self):
        # Retrieve the latest position, velocity, effort, and time (thread-safe)
        with self.lock:
            return self.last_position, self.last_velocity, self.last_effort, self.last_time

    def write(self, encoded_data):
        # Send data to the serial port (thread-safe)
        with self.write_lock:
            self.ser.write(encoded_data)

    JOINT_MIN = np.array([-math.pi/2, -math.pi/2, -math.pi*0.999, -math.pi/2, -math.pi*0.875, -math.pi/2])  # Min joint limits (radians)
    JOINT_MAX = np.array([math.pi/2, math.pi/2, math.pi*0.999, math.pi/2, math.pi*0.875, math.pi/2])  # Max joint limits (radians)

    def set_pos(self, pos):
        # Set the desired joint positions (in SI units)
        ok = True
        for i, (p, mn, mx) in enumerate(zip(pos, self.JOINT_MIN, self.JOINT_MAX)):
            if not (mn <= p <= mx):  # Check if position is within limits
                logger.error(f"Joint #{i+2} reach limit, min: {mn}, max: {mx}, current pos: {p}")
                if self.error_cb:
                    self.error_cb(f"Joint #{i+2} reach limit")  # Report error
                ok = False
        if ok:
            raw_pos = self.to_raw_unit(pos)  # Convert to raw units
            self.write(struct.pack('>BBHHHHHHxxxx', self.COMM_HEAD, self.COMM_TYPE_CTRL, *raw_pos))  # Send control packet

    def set_torque(self, torque):
        # Enable (1) or disable (0) torque
        self.write(struct.pack('>BBBxxxxxxxxxxxxxxx', self.COMM_HEAD, self.COMM_TYPE_TORQUE, torque))

    def stop(self):
        # Shut down the controller gracefully
        if not self.quit.is_set():
            self.quit.set()  # Signal thread to stop
            self.set_torque(0)  # Disable torque
            self.ser.flushOutput()  # Flush serial output
            self.ser.close()  # Close serial port

    def __del__(self):
        # Destructor to ensure proper cleanup
        self.stop()
import serial  # Library for serial communication with hardware devices
import threading  # Library for running tasks concurrently using threads
import numpy as np  # Library for numerical operations, especially with arrays
import struct  # Library for packing/unpacking binary data for serial communication
import math  # Library for mathematical functions like pi
import time  # Library for timing operations, e.g., delays
import sys  # Library for system-level operations, e.g., stdout
import logging  # Library for logging debug/info/error messages

logger = logging.getLogger(__name__)  # Create a logger specific to this module
logging.basicConfig(level=logging.INFO)  # Configure logging to show INFO level and above

class HeadController:
    # Define constants for communication protocol
    COMM_LEN = 2 + 16  # Total length of a communication packet: 2 bytes (header + type) + 16 bytes (data)
    COMM_HEAD = 0x5A  # Header byte that marks the start of a valid packet
    COMM_TYPE_PING = 0x00  # Packet type for ping request to check connection
    COMM_TYPE_PONG = 0x01  # Packet type for pong response from device
    COMM_TYPE_CTRL = 0x02  # Packet type for control commands, e.g., setting position
    COMM_TYPE_FEEDBACK = 0x03  # Packet type for feedback data, e.g., current position
    COMM_TYPE_TORQUE = 0x04  # Packet type for enabling/disabling torque

    @staticmethod
    def to_si_unit(arr):
        # Convert raw encoder values to SI units (radians)
        arr = arr.copy()  # Create a copy to avoid modifying the input array
        arr = -(np.array(arr) - 2048) / 4096 * (2 * math.pi)  # Convert 12-bit encoder (0-4095) to radians, centered at 2048
        return arr  # Return the converted array

    @staticmethod
    def to_raw_unit(arr):
        # Convert SI units (radians) back to raw encoder values
        arr = arr.copy()  # Create a copy to avoid modifying the input array
        arr = (-np.array(arr) / (2 * math.pi) * 4096 + 2048).astype(int)  # Convert radians to 12-bit raw values, centered at 2048
        return arr  # Return the converted array as integers

    def __init__(self, name):
        # Initialize the HeadController with a serial device name (e.g., '/dev/tty_head')
        logger.info(f"Using device {name}")  # Log the device being used
        self.state_cb = None  # Callback function for state updates (position, velocity, effort)
        self.pong_cb = None  # Callback function for pong responses
        self.ser = serial.Serial(name, 921600, timeout=None)  # Open serial port at 921600 baud rate, no timeout
        self.lock = threading.Lock()  # Threading lock for safe access to state variables
        self.last_position = None  # Store the last known position in SI units
        self.last_velocity = None  # Store the last known velocity
        self.last_effort = None  # Store the last known effort (like acceleration)
        self.last_time = None  # Store the timestamp of the last update
        self.write_lock = threading.Lock()  # Threading lock for serial write operations
        self.config_cb = None  # Callback for configuration updates (not used here)
        self.config_cb_lock = threading.Lock()  # Lock for config callback (not used here)
        self.debug_cb = None  # Callback for debug data outside standard packets
        self.quit = threading.Event()  # Event to signal the receive thread to stop
        self.t = threading.Thread(target=self.recv_thread, daemon=True)  # Create a daemon thread for receiving data
        self.t.start()  # Start the receive thread
        while self.last_position is None:  # Wait until initial position feedback is received
            time.sleep(0.1)  # Sleep briefly to avoid busy-waiting

    databuf = bytearray()  # Buffer for accumulating debug data outside standard packets

    def recv_thread(self):
        # Background thread to continuously receive and process serial data
        try:
            while not self.quit.is_set():  # Loop until the quit event is triggered
                data = self.ser.read(1)  # Read one byte from the serial port
                if data[0] != self.COMM_HEAD:  # Check if the byte is not a packet header
                    if data[0] in [b'\n'[0], b'\r'[0]]:  # Check for newline or carriage return
                        if len(self.databuf) > 0 and all(c in b'0123456789-., ' for c in self.databuf):  # If buffer contains valid numeric data
                            try:
                                debugdata = [float(x) for x in self.databuf.decode("ascii").split(",")]  # Parse buffer as comma-separated floats
                                if self.debug_cb:  # If a debug callback is set
                                    self.debug_cb(debugdata)  # Call the debug callback with parsed data
                            except:
                                pass  # Ignore any parsing errors
                        self.databuf = bytearray()  # Reset the debug buffer
                    else:
                        self.databuf.extend(data)  # Append the byte to the debug buffer
                    sys.stdout.buffer.write(data)  # Echo the byte to stdout
                    sys.stdout.flush()  # Flush stdout to ensure immediate output
                    continue  # Skip to the next iteration

                data += self.ser.read(self.COMM_LEN - 1)  # Read the remaining bytes of the packet
                if len(data) != self.COMM_LEN:  # Verify the packet length matches expected size
                    continue  # Skip if packet is incomplete

                if data[1] == self.COMM_TYPE_PONG:  # Check if packet is a pong response
                    if self.pong_cb:  # If a pong callback is set
                        self.pong_cb(struct.unpack('>HHxxxxxxxxxxxx', data[2:]))  # Unpack 2 uint16 values and call callback
                elif data[1] == self.COMM_TYPE_FEEDBACK:  # Check if packet is feedback data
                    position = self.to_si_unit(np.array(struct.unpack('>HHxxxxxxxxxxxx', data[2:])))  # Unpack 2 uint16 values and convert to radians
                    this_time = time.time()  # Get the current timestamp
                    with self.lock:  # Acquire lock for thread-safe state update
                        if self.last_time is None:  # If this is the first update
                            self.last_position = position  # Set initial position
                            self.last_velocity = np.zeros(2)  # Initialize velocity as zero
                            self.last_effort = np.zeros(2)  # Initialize effort as zero
                            self.last_time = this_time - 1  # Set initial time to avoid division by zero
                        else:
                            delta_time = this_time - self.last_time  # Calculate time difference
                            velocity = (position - self.last_position) / delta_time  # Compute velocity
                            effort = (velocity - self.last_velocity) / delta_time  # Compute effort (like acceleration)
                            self.last_position = position  # Update position
                            self.last_velocity = velocity  # Update velocity
                            self.last_effort = effort  # Update effort
                            self.last_time = this_time  # Update time
                        if self.state_cb:  # If a state callback is set
                            self.state_cb(self.last_position, self.last_velocity, self.last_effort, self.last_time)  # Call it with updated state
        finally:
            logger.info("Receive thread exiting")  # Log when the thread stops

    def get_pos(self):
        # Retrieve the latest position, velocity, effort, and time in a thread-safe manner
        with self.lock:  # Acquire lock to ensure consistent data
            return self.last_position, self.last_velocity, self.last_effort, self.last_time  # Return current state

    def write(self, encoded_data):
        # Send data to the serial port in a thread-safe manner
        with self.write_lock:  # Acquire lock to prevent concurrent writes
            self.ser.write(encoded_data)  # Write the encoded data to the serial port

    JOINT_MIN = np.array([-math.pi/2, -math.pi/2])  # Minimum joint limits in radians (-90 degrees)
    JOINT_MAX = np.array([math.pi/2, math.pi/2])  # Maximum joint limits in radians (+90 degrees)

    def set_pos(self, pos):
        # Set the desired joint positions in SI units (radians)
        pos_protected = np.clip(np.array(pos), self.JOINT_MIN, self.JOINT_MAX)  # Clamp positions to joint limits
        if np.allclose(pos, pos_protected, atol=0.01):  # Check if original positions are close to clamped values
            raw_pos = self.to_raw_unit(pos_protected)  # Convert clamped positions to raw units
            self.write(struct.pack('>BBHHxxxxxxxxxxxx', self.COMM_HEAD, self.COMM_TYPE_CTRL, *raw_pos))  # Pack and send control packet
        else:
            logger.error(f"Head reach min/max!!! {pos} {pos_protected}")  # Log an error if positions were clamped

    def set_torque(self, torque):
        # Enable (torque=1) or disable (torque=0) torque on the head motors
        self.write(struct.pack('>BBBxxxxxxxxxxxxxxx', self.COMM_HEAD, self.COMM_TYPE_TORQUE, torque))  # Pack and send torque packet

    def stop(self):
        # Gracefully shut down the controller
        if not self.quit.is_set():  # Check if not already stopping
            self.quit.set()  # Signal the receive thread to stop
            self.set_torque(0)  # Disable torque on the motors
            self.ser.flushOutput()  # Flush any pending output data
            self.ser.close()  # Close the serial port

    def __del__(self):
        # Destructor to ensure cleanup when the object is deleted
        self.stop()  # Call stop to clean up resources
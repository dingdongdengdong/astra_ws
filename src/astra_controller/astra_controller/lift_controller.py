import serial  # Library for serial communication with hardware devices
import threading  # Library for running tasks concurrently using threads
import numpy as np  # Library for numerical operations, especially with arrays
import struct  # Library for packing/unpacking binary data for serial communication
import time  # Library for timing operations, e.g., delays
import sys  # Library for system-level operations, e.g., stdout
import logging  # Library for logging debug/info/error messages

logger = logging.getLogger(__name__)  # Create a logger specific to this module
logging.basicConfig(level=logging.INFO)  # Configure logging to show INFO level and above

class LiftController:
    # Define constants for communication protocol
    COMM_LEN = 2 + 16  # Total length of a communication packet: 2 bytes (header + type) + 16 bytes (data)
    COMM_HEAD = 0x5A  # Header byte that marks the start of a valid packet
    COMM_TYPE_PING = 0x00  # Packet type for ping request to check connection
    COMM_TYPE_PONG = 0x01  # Packet type for pong response from device
    COMM_TYPE_CTRL = 0x02  # Packet type for control commands, e.g., setting position
    COMM_TYPE_FEEDBACK = 0x03  # Packet type for feedback data, e.g., current position

    # Define constants for lift mechanism
    STEPPER_PULSE_PER_REV = 800  # Number of stepper motor pulses per revolution
    RAIL_MM_PER_REV = 75  # Millimeters of rail movement per stepper revolution
    RAIL_MAX_LENGTH_MM = 1190  # Maximum length of the rail in millimeters
    STEPPER_MAX_PULSE = (RAIL_MAX_LENGTH_MM / RAIL_MM_PER_REV * STEPPER_PULSE_PER_REV)  # Max pulses for full rail extension (12693.33)

    @staticmethod
    def to_si_unit(x):
        # Convert raw pulse count to SI units (meters)
        return x / LiftController.STEPPER_PULSE_PER_REV * LiftController.RAIL_MM_PER_REV / 1000  # Convert pulses to meters

    @staticmethod
    def to_raw_unit(x):
        # Convert SI units (meters) to raw pulse count
        return int(x * 1000 / LiftController.RAIL_MM_PER_REV * LiftController.STEPPER_PULSE_PER_REV)  # Convert meters to pulses and round to integer

    def __init__(self, name):
        # Initialize the LiftController with a serial device name (e.g., '/dev/tty_puppet_lift_right')
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
        self.error_cb = None  # Callback function for reporting errors
        self.quit = threading.Event()  # Event to signal the receive thread to stop
        self.t = threading.Thread(target=self.recv_thread, daemon=True)  # Create a daemon thread for receiving data
        self.t.start()  # Start the receive thread
        while self.last_position is None:  # Wait until initial position feedback is received
            time.sleep(0.1)  # Sleep briefly to avoid busy-waiting

    def recv_thread(self):
        # Background thread to continuously receive and process serial data
        try:
            while not self.quit.is_set():  # Loop until the quit event is triggered
                data = self.ser.read(1)  # Read one byte from the serial port
                if data[0] != self.COMM_HEAD:  # Check if the byte is not a packet header
                    sys.stdout.buffer.write(data)  # Echo the byte to stdout
                    sys.stdout.flush()  # Flush stdout to ensure immediate output
                    continue  # Skip to the next iteration

                data += self.ser.read(self.COMM_LEN - 1)  # Read the remaining bytes of the packet
                if len(data) != self.COMM_LEN:  # Verify the packet length matches expected size
                    continue  # Skip if packet is incomplete

                if data[1] == self.COMM_TYPE_PONG:  # Check if packet is a pong response
                    if self.pong_cb:  # If a pong callback is set
                        self.pong_cb(struct.unpack('>xxHHHHHHxxxx', data))  # Unpack pong data (6 uint16 values) and call callback
                elif data[1] == self.COMM_TYPE_FEEDBACK:  # Check if packet is feedback data
                    position = self.to_si_unit(struct.unpack('>xxIxxxxxxxxxxxx', data)[0])  # Unpack 32-bit uint and convert to meters
                    this_time = time.time()  # Get the current timestamp
                    with self.lock:  # Acquire lock for thread-safe state update
                        if self.last_time is None:  # If this is the first update
                            self.last_position = position  # Set initial position
                            self.last_velocity = 0  # Initialize velocity as zero
                            self.last_effort = 0  # Initialize effort as zero
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

    def set_pos(self, pos):
        # Set the desired lift position in SI units (meters)
        max_pos = self.RAIL_MAX_LENGTH_MM / 1000  # Calculate maximum position in meters (1.19m)
        if not (0 <= pos <= max_pos):  # Check if position is within valid range
            logger.error(f"Joint #1 reach limit, min: 0, max: {max_pos}, current pos: {pos}")  # Log error if out of range
            if self.error_cb:  # If an error callback is set
                self.error_cb(f"Joint #1 reach limit")  # Call it with the error message
        else:
            raw_pos = self.to_raw_unit(pos)  # Convert position to raw pulse count
            self.write(struct.pack('>BBIxxxxxxxxxxxx', self.COMM_HEAD, self.COMM_TYPE_CTRL, raw_pos))  # Pack and send control packet

    def stop(self):
        # Gracefully shut down the controller
        if not self.quit.is_set():  # Check if not already stopping
            self.quit.set()  # Signal the receive thread to stop
            self.ser.close()  # Close the serial port

    def __del__(self):
        # Destructor to ensure cleanup when the object is deleted
        self.stop()  # Call stop to clean up resources
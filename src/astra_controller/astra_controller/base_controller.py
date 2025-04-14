import odrive_can.odrive  # ODrive CAN communication library
import threading  # Threading support for concurrent tasks
import math  # Math functions for kinematics
import time  # Time functions for delays and timing
import asyncio  # Asynchronous I/O support

import logging  # Logging for debug/info messages

logger = logging.getLogger(__name__)  # Logger for this module
logging.basicConfig(level=logging.INFO)  # Set logging level to INFO

class BaseController:
    LEFT_NODE_ID = 0  # CAN node ID for left motor
    RIGHT_NODE_ID = 1  # CAN node ID for right motor

    LEFT_INSTALL_DIR = -1  # Direction multiplier for left motor (reverses direction)
    RIGHT_INSTALL_DIR = 1  # Direction multiplier for right motor

    WHEEL_BASE = 0.44  # Distance between wheels in meters
    WHEEL_D = 0.139  # Wheel diameter in meters

    def __init__(self, name):
        # Initialize BaseController with CAN device name
        logger.info(f"Using device {name}")  # Log device name

        self.state_cb = None  # Callback for state updates (odometry)
        self.debug_cb = None  # Callback for debug data

        self.device_name = name  # Store CAN device name

        self.lock = threading.Lock()  # Lock for thread-safe velocity updates

        self.last_left_vel = None  # Last left wheel velocity
        self.last_right_vel = None  # Last right wheel velocity
        self.last_time = None  # Last update timestamp

        self.write_lock = threading.Lock()  # Lock for thread-safe position writes

        self.curpos = {self.LEFT_NODE_ID: 0, self.RIGHT_NODE_ID: 0}  # Current wheel positions (turns)
        self.setpos = {self.LEFT_NODE_ID: 0, self.RIGHT_NODE_ID: 0}  # Desired wheel positions (turns)

        self.quit = threading.Event()  # Event to signal thread termination

        # Start threads for left and right motor control
        self.t = threading.Thread(target=asyncio.run, args=(self.odrive_can_thread(self.LEFT_NODE_ID),), daemon=True)
        self.t.start()  # Start left motor thread
        self.t2 = threading.Thread(target=asyncio.run, args=(self.odrive_can_thread(self.RIGHT_NODE_ID),), daemon=True)
        self.t2.start()  # Start right motor thread

        # Wait for initialization to complete
        while True:
            with self.lock:
                if self.last_time is not None:  # Check if any motor has updated
                    break
            time.sleep(0.1)  # Brief delay to avoid busy-waiting

    def feedback_cb(self, msg: odrive_can.odrive.CanMsg, caller: odrive_can.odrive.ODriveCAN):
        # Callback for motor encoder feedback
        assert msg.name == 'Get_Encoder_Estimates'  # Ensure correct message type
        node_id = msg.axis_id  # Get motor ID (left or right)
        pos, vel = msg.data['Pos_Estimate'], msg.data['Vel_Estimate']  # Extract position and velocity

        logging.debug(f"[Node #{node_id}] pos: {pos:.3f} [turns], vel: {vel:.3f} [turns/s]")  # Log debug info
        
        self.curpos[node_id] = pos  # Update current position

        # Publish debug data if callback exists
        if node_id == self.LEFT_NODE_ID and self.debug_cb is not None:
            self.debug_cb("curpos_left", pos)  # Debug left position
        elif node_id == self.RIGHT_NODE_ID and self.debug_cb is not None:
            self.debug_cb("curpos_right", pos)  # Debug right position

        this_time = time.time()  # Current timestamp
        with self.lock:  # Thread-safe velocity update
            if self.last_time is None:  # First update
                self.last_left_vel = 0
                self.last_right_vel = 0
                self.last_time = this_time
            else:
                delta_time = this_time - self.last_time  # Time since last update

                # Update velocities based on motor ID
                if node_id == self.LEFT_NODE_ID:
                    left_vel = vel * self.LEFT_INSTALL_DIR  # Adjust direction
                    right_vel = self.last_right_vel  # Use last known value
                else:
                    left_vel = self.last_left_vel  # Use last known value
                    right_vel = vel * self.RIGHT_INSTALL_DIR  # Adjust direction

                # Convert wheel velocities to robot velocities (differential drive)
                linear_vel = (left_vel + right_vel) / 2 * (math.pi * self.WHEEL_D)  # Linear velocity (m/s)
                angular_vel = (right_vel - left_vel) / 2 * (math.pi * self.WHEEL_D) / (self.WHEEL_BASE / 2)  # Angular velocity (rad/s)

                # Store updated velocities
                if node_id == self.LEFT_NODE_ID:
                    self.last_left_vel = left_vel
                else:
                    self.last_right_vel = right_vel
                self.last_time = this_time
                if self.state_cb is not None:
                    self.state_cb(linear_vel, angular_vel, delta_time)  # Call odometry callback

    async def odrive_can_thread(self, node_id):
        # Asynchronous thread to manage ODrive motor for a given node ID
        drv = odrive_can.odrive.ODriveCAN(node_id, self.device_name)  # Initialize ODrive CAN interface

        await drv.start()  # Start CAN communication

        logger.info("Clearing errors")  # Log error clearing
        drv.clear_errors()  # Clear any existing errors
        drv.check_errors()  # Check for errors after clearing

        drv.set_linear_count(0)  # Reset encoder position to zero

        drv.set_controller_mode("POSITION_CONTROL", "TRAP_TRAJ")  # Set to position control with trapezoidal trajectory

        drv.set_pos_gain(20.0)  # Set position gain for control
        drv.set_vel_gains(0.1, 0)  # Set velocity gains (P, I)
        drv.set_traj_vel_limit(20)  # Set max velocity for trajectory (turns/s)
        drv.set_traj_accel_limits(1, 1)  # Set accel/decel limits (turns/s^2)

        drv.set_axis_state_no_wait("CLOSED_LOOP_CONTROL")  # Enter closed-loop control mode
        
        # Wait until motor enters closed-loop state
        while drv.axis_state != "CLOSED_LOOP_CONTROL":
            drv.check_errors()  # Check for errors during transition
            await asyncio.sleep(0.1)  # Brief delay

        drv.feedback_callback = self.feedback_cb  # Assign feedback callback

        logger.info("Running base control")  # Log start of control loop
        try:
            while True:
                if self.quit.is_set():  # Check for shutdown signal
                    raise Exception("quit")
                with self.write_lock:  # Thread-safe position update
                    drv.set_input_pos(self.setpos[node_id])  # Set motor position
                drv.check_errors()  # Check for errors after command
                await asyncio.sleep(0.1)  # Control loop rate (10 Hz)
        finally:
            drv.stop()  # Stop motor on exit

    def set_vel(self, linear_vel, angular_vel):
        # Convert robot velocities to wheel velocities (differential drive)
        left_vel = (linear_vel - angular_vel * self.WHEEL_BASE / 2) / (math.pi * self.WHEEL_D) * self.LEFT_INSTALL_DIR  # Left wheel velocity (turns/s)
        right_vel = (linear_vel + angular_vel * self.WHEEL_BASE / 2) / (math.pi * self.WHEEL_D) * self.RIGHT_INSTALL_DIR  # Right wheel velocity (turns/s)
        
        TIME_DELTA = 0.1  # Time step for position update (s)
        MAX_POS_DIFF_IN_TURNS = 2  # Max allowed position difference (turns)

        with self.write_lock:  # Thread-safe position update
            self.setpos[self.LEFT_NODE_ID] += left_vel * TIME_DELTA  # Update left setpoint
            self.setpos[self.RIGHT_NODE_ID] += right_vel * TIME_DELTA  # Update right setpoint
            
            # Clamp setpoints to prevent large jumps
            if self.setpos[self.LEFT_NODE_ID] > self.curpos[self.LEFT_NODE_ID] + MAX_POS_DIFF_IN_TURNS:
                self.setpos[self.LEFT_NODE_ID] = self.curpos[self.LEFT_NODE_ID] + MAX_POS_DIFF_IN_TURNS
                logger.info(f"Left setpos clamped to {self.setpos[self.LEFT_NODE_ID]}")
            if self.setpos[self.LEFT_NODE_ID] < self.curpos[self.LEFT_NODE_ID] - MAX_POS_DIFF_IN_TURNS:
                self.setpos[self.LEFT_NODE_ID] = self.curpos[self.LEFT_NODE_ID] - MAX_POS_DIFF_IN_TURNS
                logger.info(f"Left setpos clamped to {self.setpos[self.LEFT_NODE_ID]}")
            if self.setpos[self.RIGHT_NODE_ID] > self.curpos[self.RIGHT_NODE_ID] + MAX_POS_DIFF_IN_TURNS:
                self.setpos[self.RIGHT_NODE_ID] = self.curpos[self.RIGHT_NODE_ID] + MAX_POS_DIFF_IN_TURNS
                logger.info(f"Right setpos clamped to {self.setpos[self.RIGHT_NODE_ID]}")
            if self.setpos[self.RIGHT_NODE_ID] < self.curpos[self.RIGHT_NODE_ID] - MAX_POS_DIFF_IN_TURNS:
                self.setpos[self.RIGHT_NODE_ID] = self.curpos[self.RIGHT_NODE_ID] - MAX_POS_DIFF_IN_TURNS
                logger.info(f"Right setpos clamped to {self.setpos[self.RIGHT_NODE_ID]}")

        # Publish debug data if callback exists
        if self.debug_cb is not None:
            self.debug_cb("setpos_left", self.setpos[self.LEFT_NODE_ID])  # Debug left setpoint
            self.debug_cb("setpos_right", self.setpos[self.RIGHT_NODE_ID])  # Debug right setpoint

    def stop(self):
        # Stop motor control threads
        if not self.quit.is_set():
            self.quit.set()  # Signal threads to quit
            time.sleep(0.1)  # Allow time for threads to stop

    def __del__(self):
        # Destructor to ensure cleanup
        self.stop()  # Stop motors on object deletion
import threading  # Threading support for camera feed
import time  # Time functions for frame rate calculation
import rclpy  # ROS 2 Python client library
import rclpy.node  # Node class for ROS nodes
import rclpy.qos  # QoS settings for ROS communication
import rclpy.action  # Action support (not used here)

import sensor_msgs.msg  # Sensor messages (e.g., Image)

import cv2  # OpenCV library for camera capture

def feed(node, pub, device, image_width, image_height, framerate, resize_image_width, resize_image_height):
    # Function to capture and publish camera feed in a separate thread
    cam = cv2.VideoCapture(device, cv2.CAP_V4L2)  # Open camera device with V4L2 backend
    cam.set(cv2.CAP_PROP_BUFFERSIZE, 10)  # Set buffer size to 10 frames

    fourcc_value = cv2.VideoWriter_fourcc(*'MJPG')  # Define MJPG codec

    cam.set(cv2.CAP_PROP_FOURCC, fourcc_value)  # Set camera to MJPG format
    cam.set(cv2.CAP_PROP_FRAME_WIDTH, image_width)  # Set frame width
    cam.set(cv2.CAP_PROP_FRAME_HEIGHT, image_height)  # Set frame height
    cam.set(cv2.CAP_PROP_FPS, framerate)  # Set frame rate
    
    assert cam.isOpened()  # Ensure camera opened successfully
    
    start_time = time.perf_counter()  # Start time for frame rate calculation
    
    while True:
        ret, image = cam.read()  # Read frame from camera
        if not ret:  # Skip if frame read fails
            continue
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)  # Convert from BGR to RGB
            
        msg = sensor_msgs.msg.Image()  # Create ROS Image message
        msg.header.stamp = node.get_clock().now().to_msg()  # Current timestamp
        msg.header.frame_id = "default_cam"  # Frame ID for camera
        
        # Resize image if specified, otherwise use original dimensions
        if resize_image_width:
            image = cv2.resize(image, (resize_image_width, resize_image_height))  # Resize image
            msg.width = resize_image_width  # Set message width
            msg.height = resize_image_height  # Set message height
        else:
            msg.width = image_width  # Use original width
            msg.height = image_height  # Use original height
        
        msg.encoding = "rgb8"  # Set encoding to RGB 8-bit
        msg.data.frombytes(image.tobytes())  # Convert image to bytes for ROS message

        pub.publish(msg)  # Publish image message
        
        print(1 / (time.perf_counter() - start_time))  # Print frame rate (FPS)
        start_time = time.perf_counter()  # Reset start time

def main(args=None):
    rclpy.init(args=args)  # Initialize ROS 2

    node = rclpy.node.Node('cam_node')  # Create ROS node named 'cam_node'

    # Declare parameters with defaults
    node.declare_parameter('device', '/dev/video_head')  # Camera device path
    node.declare_parameter('image_width', 640)  # Default image width
    node.declare_parameter('image_height', 360)  # Default image height
    node.declare_parameter('framerate', 30.0)  # Default frame rate
    node.declare_parameter('resize_image_width', 0)  # Resize width (0 = no resize)
    node.declare_parameter('resize_image_height', 0)  # Resize height (0 = no resize)

    # Retrieve parameter values
    device = node.get_parameter('device').value
    image_width = node.get_parameter('image_width').value
    image_height = node.get_parameter('image_height').value
    framerate = node.get_parameter('framerate').value
    resize_image_width = node.get_parameter('resize_image_width').value
    resize_image_height = node.get_parameter('resize_image_height').value

    pub = node.create_publisher(sensor_msgs.msg.Image, "image_raw", 10)  # Publisher for raw images

    # Start camera feed in a separate thread
    threading.Thread(target=feed, args=(
        node, pub, device, image_width, image_height, framerate, resize_image_width, resize_image_height
    ), daemon=True).start()
        
    try:
        rclpy.spin(node)  # Run ROS event loop
    except KeyboardInterrupt as err:
        raise err  # Re-raise interrupt

    node.destroy_node()  # Clean up node
    rclpy.shutdown()  # Shutdown ROS

if __name__ == '__main__':
    main()  # Entry point
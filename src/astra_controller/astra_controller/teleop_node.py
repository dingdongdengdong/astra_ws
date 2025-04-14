import rclpy  # ROS 2 Python client library for node creation and communication
import rclpy.node  # Base class for creating ROS nodes
import rclpy.publisher  # Publisher class for publishing messages

import geometry_msgs.msg  # ROS messages for geometry (e.g., PoseStamped)
from astra_teleop.process import get_process  # Function to get camera processing object
from pytransform3d import transformations as pt  # 3D transformation library
import numpy as np  # Numerical operations library
from pprint import pprint  # Pretty-print for debugging

def main(args=None):
    # Main function to initialize and run the ROS node
    rclpy.init(args=args)  # Initialize ROS 2 runtime
    
    node = rclpy.node.Node("teleop_node")  # Create a ROS node named "teleop_node"

    # Publishers for camera and goal poses
    pub_cam = node.create_publisher(geometry_msgs.msg.PoseStamped, "cam_pose", 10)  # Camera pose topic
    pub = node.create_publisher(geometry_msgs.msg.PoseStamped, "goal_pose", 10)  # Goal pose topic

    def pub_T(pub: rclpy.publisher.Publisher, T):
        # Helper function to publish a transformation as a PoseStamped message
        msg = geometry_msgs.msg.PoseStamped()
        msg.header.frame_id = 'base_link'  # Frame ID
        msg.header.stamp = node.get_clock().now().to_msg()  # Timestamp
        pq = pt.pq_from_transform(T)  # Convert to position-quaternion
        msg.pose.position.x = pq[0]  # Position x
        msg.pose.position.y = pq[1]  # Position y
        msg.pose.position.z = pq[2]  # Position z
        msg.pose.orientation.w = pq[3]  # Quaternion w
        msg.pose.orientation.x = pq[4]  # Quaternion x
        msg.pose.orientation.y = pq[5]  # Quaternion y
        msg.pose.orientation.z = pq[6]  # Quaternion z
        pub.publish(msg)  # Publish the message

    Tcamgoal_last = None  # Store the last camera-to-goal transformation for smoothing

    def cb(Tcamgoal):
        # Callback to process camera-to-goal transformation and publish poses
        # Define transformation from base_link to camera (Tscam)
        Tscam = np.array([
            [0, 0, -1, 1.5],  # Rotation and translation to position the camera
            [1, 0, 0, -0.5], 
            [0, -1, 0, 0.5], 
            [0, 0, 0, 1], 
        ])
        pub_T(pub_cam, Tscam)  # Publish camera pose

        nonlocal Tcamgoal_last  # Access the last transformation
        if Tcamgoal_last is None:
            Tcamgoal_last = Tcamgoal  # Initialize with first value
        low_pass_coff = 0.4  # Low-pass filter coefficient for smoothing
        # Smooth the transformation using spherical linear interpolation (slerp)
        Tcamgoal = pt.transform_from_pq(pt.pq_slerp(
            pt.pq_from_transform(Tcamgoal_last),  # Previous transformation
            pt.pq_from_transform(Tcamgoal),  # Current transformation
            low_pass_coff  # Interpolation factor
        ))
        Tcamgoal_last = Tcamgoal  # Update the last transformation
        
        Tsgoal = Tscam @ Tcamgoal  # Compute goal pose in base_link frame
        pub_T(pub, Tsgoal)  # Publish goal pose

    # Initialize camera processing with device and calibration data
    process = get_process(device="/dev/video0", calibration_directory="./calibration_images", debug=False)
    while True:
        # Continuously process camera data to get tag-to-camera transformations
        tag2cam_left, tag2cam_right = process()
        pprint(tag2cam_left)  # Debug: print left tag transformation
        pprint(tag2cam_right)  # Debug: print right tag transformation
        cb(tag2cam_right)  # Process right tag transformation

    rclpy.spin(node)  # Unreachable due to infinite loop above

    node.destroy_node()  # Clean up the node (optional)
    rclpy.shutdown()  # Shut down ROS 2 runtime

if __name__ == '__main__':
    main()  # Run the main function
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import time

class HelloPublisher(Node):
  def __init__(self):
    super().__init__('hello_publisher')
    my_publisher=self.create_publisher(String, '/my_test_topic',10)

    self.get_logger().info('hello after 5sec')
    time.sleep(5)
    msg = String()
    msg.data = 'Hello, AhaRobot!'
    my_publisher.publish(msg)
    self.get_logger().info(f"메시지 발행 완료~{msg.data}")


def main(args=None):
    rclpy.init(args=args)
    node = HelloPublisher()
    rclpy.spin_once(node, timeout_sec=10)
    
    node.destroy_node()
    rclpy.shutdown()




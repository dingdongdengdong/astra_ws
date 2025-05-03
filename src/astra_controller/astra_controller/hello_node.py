import rclpy
from rclpy.node import Node
from std_msgs.msg import String

class HelloSubscriber(Node):
  def __init__(self):
    super().__init__('hello_subscriber')
    self.subscription=self.create_subscription(
      String,
      '/my_test_topic',
      self.hello_callback,
      10
    )
  def hello_callback(self, msg):
    self.get_logger().info(f'메시지 수신 완료~"{msg.data}')

def main(args=None):
  rclpy.init(args=args)
  node=HelloSubscriber()
  rclpy.spin(node)
  node.destroy_node()
  rclpy.shutdown()

from rclpy.node import Node

class LedSubscriber(Node):

    def __init__(self, backend_clients):
        super().__init__('led_subscriber')
        
        self.backend_clients = backend_clients
        self.led_client = self.backend_clients['led']

        self.get_logger().info("LedSubscriber initialized")

    def change_brightness(self, brightness: int):
        try:
            self.get_logger().info(f"💡 Setting brightness: {brightness}")
            self.led_client.set_brightness(brightness)
        except Exception as e:
            self.get_logger().error(f"Brightness change failed: {e}")


    def change_color(self, color):
        try:
            self.get_logger().info(f"🎨 Setting color: {color}")
            self.led_client.set_color(color)
        except Exception as e:
            self.get_logger().error(f"Color change failed: {e}")


    def led_on(self):
        self.led_client.on()

    def led_off(self):
        self.led_client.off()

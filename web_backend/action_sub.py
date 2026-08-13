import threading
import time
from rclpy.node import Node


class ActionSubscriber(Node):
    """
    ROS2-style subscriber that wraps DDSBackend and SportClient actions.
    """

    def __init__(self, backend_clients, topic_name: str = "/run_action"):
        super().__init__('action_subscriber')

        # --- Initialize DDS/WebRTC backend ---
        
        self.backend_clients = backend_clients
        self.available_actions = list(self.backend_clients['actions'].keys())
        self.topic_name = topic_name
        self.latest_command = None
        self._lock = threading.Lock()

        self.get_logger().info(f"ActionSubscriber initialized with actions: \n {self.available_actions} \n")

        # --- Start background thread to execute actions ---
        self._thread = threading.Thread(target=self._process_actions, daemon=True)
        self._thread.start()

    def send_action_command(self, action_name: str):
        """
        Queue an action to be executed by the SportClient.
        Returns True if action is valid, False otherwise.
        """
        if action_name not in self.available_actions:
            self.get_logger().warn(f"Unknown action: {action_name}")
            return False

        with self._lock:
            self.latest_command = action_name
        return True

    def _process_actions(self):
        """
        Background thread: watches for new commands and executes them.
        Runs each action in a separate thread to avoid blocking.
        """
        while True:
            if self.latest_command:
                with self._lock:
                    action_to_run = self.latest_command
                    self.latest_command = None

                try:
                    self.get_logger().info(f"Executing action: {action_to_run}")
                    threading.Thread(target=self.backend_clients['actions'][action_to_run]).start()
                except Exception as e:
                    self.get_logger().error(f"Failed to execute action {action_to_run}: {e}")

            time.sleep(0.05)  # small delay to reduce CPU usage
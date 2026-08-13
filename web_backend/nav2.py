from nav2_msgs.action import NavigateToPose, NavigateThroughPoses
from rclpy.action import ActionClient
from geometry_msgs.msg import PoseStamped
import math
from rclpy.node import Node
from config import POSE_HEADER_FRAME_ID


class Nav2Controller(Node):
    def __init__(self):
        super().__init__('web_nav_client')
        self.single_client = ActionClient(self, NavigateToPose, 'navigate_to_pose')
        self.multi_client  = ActionClient(self, NavigateThroughPoses, 'navigate_through_poses')
        self.get_logger().info("Nav2Controller initialized")

    def _pose(self, x, y, yaw):
        p = PoseStamped()
        p.header.frame_id = POSE_HEADER_FRAME_ID
        p.pose.position.x = float(x)
        p.pose.position.y = float(y)
        p.pose.orientation.z = math.sin(yaw / 2)
        p.pose.orientation.w = math.cos(yaw / 2)
        return p

    def go_to(self, wp):
        self.single_client.wait_for_server()
        goal = NavigateToPose.Goal()
        goal.pose = self._pose(wp["x"], wp["y"], wp["yaw"])
        self.single_client.send_goal_async(goal)

    def run_route(self, waypoints):
        self.multi_client.wait_for_server()
        goal = NavigateThroughPoses.Goal()
        goal.poses = [self._pose(w["x"], w["y"], w["yaw"]) for w in waypoints]
        self.multi_client.send_goal_async(goal)



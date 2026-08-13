import numpy as np
import sensor_msgs_py.point_cloud2 as pc2
from rclpy.node import Node
from sensor_msgs.msg import PointCloud2
from config import LIDAR, LIDAR_MAX_POINTS


class RosLidarSubscriber(Node):
    def __init__(self, topic_name: str):
        super().__init__('lidar_subscriber')
        self.all_points = np.empty((0, 3), dtype=np.float32)
        self.get_logger().info("RosLidarSubscriber initialized")

        self.lidar_subscription = self.create_subscription(
            PointCloud2,
            LIDAR,                     #enter lidar topic name
            f'{topic_name}',  
            self.lidar_callback,
            10
        )

    def lidar_callback(self, msg: PointCloud2):
        points_gen = pc2.read_points(msg, field_names=("x", "y", "z"), skip_nans=True)
        points_list = list(points_gen)
        if len(points_list) == 0:
            return

        # Convert to Nx3 float array
        points_array = np.array([[p[0], p[1], p[2]] for p in points_list], dtype=np.float32)

        # Downsample if too many points
        max_points = LIDAR_MAX_POINTS
        if len(points_array) > max_points:
            indices = np.random.choice(len(points_array), max_points, replace=False)
            points_array = points_array[indices]

        self.all_points = points_array
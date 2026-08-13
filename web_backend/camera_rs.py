import cv2
import numpy as np
from cv_bridge import CvBridge
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
from sensor_msgs.msg import Image
from ultralytics import YOLO
from config import YOLO_MODEL, YOLO_MODE, REALSENSE_CAMERA_COLOR, REALSENSE_CAMERA_DEPTH

class RosRSImageSubscriber(Node):
    def __init__(self):
        super().__init__('rs_image_subscriber')

        self.qos_profile = QoSProfile(
            reliability=ReliabilityPolicy.RELIABLE,
            history=HistoryPolicy.KEEP_LAST,
            depth=10
        )

        self.bridge = CvBridge()
        self.color_frame = None
        self.depth_frame = None
        self.model = YOLO(YOLO_MODEL) 
        self.detection_frame = None
        
        self.get_logger().info("Started RosImageSubscriber for RealSense Camera stream")


        self.color_sub = self.create_subscription(
            Image,
            REALSENSE_CAMERA_COLOR,
            self.color_callback,
            self.qos_profile
        )

        self.depth_sub = self.create_subscription(
            Image,
            REALSENSE_CAMERA_DEPTH,
            self.depth_callback,
            self.qos_profile
        )


    def color_callback(self, msg):
        try:
            self.color_frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
            
            if YOLO_MODE=="rs":
                results = self.model(self.color_frame, verbose=False)
                self.detection_frame = results[0].plot()

        except Exception as e:
            self.get_logger().error(f"Failed to convert color image: {e}")


    def depth_callback(self, msg):
        try:
            self.depth_frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding='passthrough')

        except Exception as e:
            self.get_logger().error(f"Failed to convert depth image: {e}")


    def get_distance_at_pixel(self, x, y):
        """Returns distance in meters at pixel (x, y), or None if unavailable"""
        if self.depth_frame is None:
            return None
        distance_mm = self.depth_frame[y, x]
        return distance_mm / 1000.0


    def get_colorized_depth(self):
        """Returns a BGR heatmap of the depth frame for visualization"""
        if self.depth_frame is None:
            return None
        normalized = cv2.normalize(self.depth_frame, None, 0, 255, cv2.NORM_MINMAX)
        normalized = np.uint8(normalized)
        return cv2.applyColorMap(normalized, cv2.COLORMAP_JET)

    def destroy_node(self):
        super().destroy_node()

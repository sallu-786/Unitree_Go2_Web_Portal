#!/usr/bin/env python3
"""
AprilTag Inspection Node for Go2
- Detects AprilTag → corrects drift → triggers LLM inspection photo
Fits into your existing DataStream / Nav2 stack.
"""

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
from unitree_go.msg import WirelessController  # your CMD_VEL type
import cv2
import numpy as np
import base64
import time
import threading
from pupil_apriltags import Detector

# ── Match your config.py values ─────────────────────────────────────────────
CAMERA_TOPIC  = "/frontvideostream"
CMD_TOPIC     = "/wirelesscontroller"
TARGET_TAG_ID = 0
TAG_FAMILY    = "tag36h11"
TAG_SIZE      = 0.15        # meters — measure your printed tag

# Camera intrinsics — get from: ros2 topic echo /camera/camera_info
FX, FY = 462.0, 462.0
CX, CY = 370.0, 290.0      # IMAGE_WIDTH/2, IMAGE_HEIGHT/2 approx

# Control
TARGET_DIST   = 1.0         # stop this far from tag (meters)
KP_YAW        = 0.003
KP_FWD        = 0.4
ALIGN_TOL_PX  = 15          # pixel tolerance for "centered"
ALIGN_TOL_M   = 0.05        # distance tolerance in meters
# ─────────────────────────────────────────────────────────────────────────────


class AprilTagInspector(Node):

    def __init__(self, llm_system=None, image_subscriber=None):
        super().__init__("apriltag_inspector")
        self.bridge      = CvBridge()
        self.detector    = Detector(families=TAG_FAMILY)
        self.llm         = llm_system        # pass your GenerateResponse() instance
        self.img_sub_ext = image_subscriber  # pass your RosImageSubscriber() if already running

        # State machine: SEARCHING → CORRECTING → ALIGNED → INSPECTING → DONE
        self.state       = "SEARCHING"
        self.last_frame  = None
        self._lock       = threading.Lock()

        # Publisher — using your WirelessController topic
        self.cmd_pub = self.create_publisher(WirelessController, CMD_TOPIC, 10)

        # Only subscribe directly if no external subscriber passed in
        if self.img_sub_ext is None:
            self.create_subscription(Image, CAMERA_TOPIC, self._image_cb, 10)
        else:
            # Poll external subscriber in a timer instead
            self.create_timer(0.05, self._poll_external_frame)

        self.get_logger().info(f"AprilTagInspector ready | watching tag ID={TARGET_TAG_ID}")

    # ── Frame ingestion ──────────────────────────────────────────────────────

    def _image_cb(self, msg: Image):
        frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding="bgr8")
        with self._lock:
            self.last_frame = frame
        self._process()

    def _poll_external_frame(self):
        frame = self.img_sub_ext.color_frame
        if frame is None:
            return
        with self._lock:
            self.last_frame = frame
        self._process()

    # ── Core logic ───────────────────────────────────────────────────────────

    def _process(self):
        if self.state == "DONE":
            return

        with self._lock:
            frame = self.last_frame.copy() if self.last_frame is not None else None
        if frame is None:
            return

        gray       = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        detections = self.detector.detect(
            gray,
            estimate_tag_pose=True,
            camera_params=(FX, FY, CX, CY),
            tag_size=TAG_SIZE,
        )

        tag = next((d for d in detections if d.tag_id == TARGET_TAG_ID), None)

        if tag is None:
            if self.state == "CORRECTING":
                self._stop()   # lost tag mid-correction, stop safely
                self.state = "SEARCHING"
            return

        # ── Measurements ────────────────────────────────────────────────────
        x_error  = tag.center[0] - (frame.shape[1] / 2)   # pixels, + = right
        distance = float(tag.pose_t[2][0])                  # meters

        centered  = abs(x_error)  < ALIGN_TOL_PX
        at_target = abs(distance - TARGET_DIST) < ALIGN_TOL_M

        self.get_logger().info(
            f"[{self.state}] tag={tag.tag_id} dist={distance:.2f}m "
            f"x_err={x_error:.0f}px centered={centered} at_target={at_target}"
        )

        # ── State transitions ────────────────────────────────────────────────
        if self.state in ("SEARCHING", "CORRECTING"):
            if centered and at_target:
                self._stop()
                self.state = "ALIGNED"
                self.get_logger().info("✓ Aligned! Triggering inspection...")
                threading.Thread(target=self._do_inspection, args=(frame,), daemon=True).start()
            else:
                self.state = "CORRECTING"
                self._send_correction(x_error, distance)

    # ── Motion ───────────────────────────────────────────────────────────────

    def _send_correction(self, x_error, distance):
        cmd = WirelessController()
        # Map to lx (forward) and rx (yaw) — adjust field names to your msg definition
        cmd.lx = float(np.clip(KP_FWD * (distance - TARGET_DIST), -0.3, 0.3))
        cmd.rx = float(np.clip(-KP_YAW * x_error, -0.5, 0.5))
        self.cmd_pub.publish(cmd)

    def _stop(self):
        self.cmd_pub.publish(WirelessController())  # all zeros = stop

    # ── Inspection ───────────────────────────────────────────────────────────

    def _do_inspection(self, frame: np.ndarray):
        self.state = "INSPECTING"

        # Encode frame for LLM
        _, buf    = cv2.imencode(".jpg", cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        img_b64   = base64.b64encode(buf).decode("utf-8")
        data_url  = f"data:image/jpeg;base64,{img_b64}"

        # Save raw image locally
        ts        = time.strftime("%Y%m%d_%H%M%S")
        save_path = f"/tmp/inspection_tag{TARGET_TAG_ID}_{ts}.jpg"
        cv2.imwrite(save_path, frame)
        self.get_logger().info(f"📸 Saved inspection image: {save_path}")

        # LLM analysis (reuses your GenerateResponse from DataStream)
        if self.llm is not None:
            result = self.llm.llm_response(
                "You are inspecting a factory environment. "
                "Describe what you see. Check for: safety equipment (helmets, glasses, jackets), "
                "hazards, unusual equipment states. Be concise. Respond in Japanese.",
                data_url
            )
            self.get_logger().info(f"🔍 Inspection result:\n{result}")
        else:
            self.get_logger().info("No LLM attached — image saved, skipping analysis.")

        self.state = "DONE"
        self.get_logger().info("✅ Inspection complete.")


# ── Standalone runner ────────────────────────────────────────────────────────

def main():
    rclpy.init()
    node = AprilTagInspector()          # standalone, no LLM
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node._stop()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
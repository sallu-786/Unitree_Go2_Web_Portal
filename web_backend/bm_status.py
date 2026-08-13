from rclpy.node import Node
from unitree_go.msg import LowState
from std_msgs.msg import String
import json

class BatteryMotorStatus(Node):
    def __init__(self, lf_lowcmd_topic_name: str):
        super().__init__('Battery_status_and_joint_motor_temperature_status')

        # Data storage
        self.battery = None
        self.motor_status = None

        # NEW: IMU
        self.roll = None
        self.pitch = None
        self.yaw = None

        self.voltage = None
        self.current = None
        self.power = None
        self.get_logger().info("BatteryMotorStatus initialized")

        self.multiple_state = None

        # -------------------- SUBSCRIBERS --------------------
        self.create_subscription(
            LowState,
            "/lf/lowstate",
            self.lf_lowcmd_callback,
            10
        )

        self.create_subscription(
            String,
            "/multiplestate",
            self.multiplestate_callback,
            10
        )


    # =========================================================
    # CALLBACK
    # =========================================================
    def lf_lowcmd_callback(self, msg):
        # Battery
        self.battery = msg.bms_state.soc

        # Motors (mode 1 only)
        self.motor_status = [m.temperature for m in msg.motor_state if m.mode == 1]

        # IMU (rpy)
        self.roll = msg.imu_state.rpy[0]
        self.pitch = msg.imu_state.rpy[1]
        self.yaw = msg.imu_state.rpy[2]

        # Power
        self.voltage = msg.power_v
        self.current = msg.power_a
        self.power = self.voltage * self.current

    def multiplestate_callback(self, msg):
        try:
            self.multiple_state = json.loads(msg.data)
        except Exception as e:
            self.get_logger().warn(f"Failed to parse multiplestate: {e}")


    def get_battery_color(self, bat):
        if bat >= 70:
            return "🟢"
        elif bat >= 30:
            return "🟡"
        elif bat >= 20:
            return "🔴"
        else:
            return "Baterry dying 🚨"

    def get_temp_color(self, temp):
        if temp <= 50:
            return "🟢"
        elif temp <= 65:
            return "🟡"
        elif temp <= 80:
            return "🔴"
        else:
            return "🚨"

    def get_tilt_color(self, val):
        val = abs(val)
        if val < 0.1:
            return "🟢"
        elif val < 0.25:
            return "🟡"
        elif val < 0.5:
            return "🔴"
        else:
            return "🚨"
        
    def get_power_color(self, power):
        if power < 50:
            return "🟢"
        elif power < 150:
            return "🟡"
        elif power < 300:
            return "🔴"
        else:
            return "🚨"

    
    def get_battery_data(self):
        if self.battery is None:
            return "Waiting for battery status..."

        # Battery part
        battery_text = f"🔋 {self.get_battery_color(self.battery)} {self.battery} %"

        # Power part (if available)
        if self.power is not None:
            power_text = (
                f" 🔌 {self.get_power_color(self.power)} {self.power:.1f} W "
                f"({self.voltage:.1f}V, {self.current:.1f}A)"
            )

            # 🚨 warning
            if self.power > 300:
                power_text += " 🚨"

            return battery_text + power_text

        return battery_text

    # =========================================================
    # MOTOR
    # =========================================================
    def get_motor_data(self):
        if self.motor_status is None:
            return "Waiting for Motor status..."

        legs = ["FL ", "FR ", "RL ", "RR "]

        output = []

        for i, leg in enumerate(legs):
            base = i * 3

            line = ( 
                f"{leg} : "
                f"hip: {self.get_temp_color(self.motor_status[base])} {self.motor_status[base]}°C, "
                f"thigh: {self.get_temp_color(self.motor_status[base+1])} {self.motor_status[base+1]}°C, "
                f"calf: {self.get_temp_color(self.motor_status[base+2])} {self.motor_status[base+2]}°C"
            )

            output.append(line)

        return "\n".join(output)

    # =========================================================
    # IMU / ORIENTATION
    # =========================================================
    def get_orientation_data(self):
        if self.roll is None:
            return "Waiting for IMU..."

        text = (
            f"Roll: {self.roll:.3f}\t" # {self.get_tilt_color(self.roll)} 
            f" Pitch: {self.pitch:.3f}\t" #{self.get_tilt_color(self.pitch)}
            f"Yaw: {self.yaw:.3f}"
        )

        # Stability warning
        if abs(self.roll) > 0.5 or abs(self.pitch) > 0.5:
            text += "\n🚨 Robot UNSTABLE!"

        return text
    
    def get_system_state_data(self):
        if self.multiple_state is None:
            return "Waiting for system state..."

        state = self.multiple_state

        def on_off(val):
            return "🟢 ON" if val else "🔴 OFF"

        text = (

            f"🚧 Obstacle Avoid: {on_off(state.get('obstaclesAvoidSwitch'))}"
            
        )

        return text

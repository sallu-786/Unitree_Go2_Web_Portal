import time
import json
import numpy as np
import cv2
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from unitree_sdk2py.sdk.sdk import create_standard_sdk
from unitree_sdk2py.idl.idl_dataclass import IDLDataClass
from unitree_sdk2py.core.dds.channel import DDSChannelFactoryInitialize, DDSCommunicator

from unitree_sdk2py.go2.audiohub.audiohub_client import AudioHubClient
from unitree_sdk2py.go2.video.video_client import VideoClient
from unitree_sdk2py.go2.sport.sport_client import SportClient
from unitree_sdk2py.go2.vui.vui_client import VuiClient
# from unitree_sdk2py.go2.vui.vui_api import VUI_COLOR

class DDSBackend:
    def __init__(self):
        self.name = "DDS"
        self.idl_data_class = IDLDataClass()
        self.sdk = create_standard_sdk('UnitreeGo2SDK')
        self.communicator = DDSChannelFactoryInitialize(domainId=0)
        self.robot = self.sdk.create_robot(self.communicator, serialNumber='B42D2000XXXXXXXX')


    def initialize(self):
        audio_client = self.robot.ensure_client(AudioHubClient.default_service_name)
        video_client = self.robot.ensure_client(VideoClient.default_service_name)
        sport_client = self.robot.ensure_client(SportClient.default_service_name)
        vui_client   = self.robot.ensure_client(VuiClient.default_service_name)

        audio_client.Init()
        video_client.Init()
        sport_client.Init()
        vui_client.Init()

        # ── helpers ──────────────────────────────────────────────────────────────
        def safe_action(fn, require_stand=True, delay=0.5):
            def wrapper():
                try:
                    if require_stand:
                        sport_client.RecoveryStand()   # ← was StandUp
                        time.sleep(delay)
                    return fn()
                except Exception as e:
                    print(f"[ERROR] Action failed: {e}")
            return wrapper

        # ── gait functions (ALL defined before actions dict) ─────────────────────
        def ensure_locomotion():
            try:
                sport_client.RecoveryStand()
                time.sleep(0.5)
                sport_client.ContinuousGait(1)
                time.sleep(0.2)
            except Exception as e:
                print(f"[WARN] ensure_locomotion failed: {e}")

        def recovery_stand():
            sport_client.RecoveryStand()

        def trot():
            ensure_locomotion()
            sport_client.SwitchGait(1)
            time.sleep(0.3)
            sport_client.Move(0, 0, 0)

        def run():
            ensure_locomotion()
            sport_client.SwitchGait(2)
            time.sleep(0.3)
            sport_client.ContinuousGait(1)
            time.sleep(0.2)
            sport_client.Move(0, 0, 0)

        def climb_stairs():
            ensure_locomotion()
            sport_client.FootRaiseHeight(0.12)
            sport_client.SwitchGait(3)
            time.sleep(0.3)
            sport_client.Move(0, 0, 0)

        def down_stairs():
            ensure_locomotion()
            sport_client.SwitchGait(4)
            time.sleep(0.3)
            sport_client.Move(0, 0, 0)

        def stop():
            sport_client.StopMove()
            sport_client.ContinuousGait(0)

        # ── actions dict (AFTER all functions are defined) ────────────────────────
        actions = {
            "Stand Up":       sport_client.RecoveryStand,
            "Stand Down":     sport_client.StandDown,
            "Sit":            sport_client.Sit,
            "Stop":           stop,

            "Wave":           safe_action(sport_client.Hello),
            "Hello":          safe_action(sport_client.Hello),
            "Heart":          safe_action(sport_client.Heart),
            "Stretch":        safe_action(sport_client.Stretch),

            "Dance1":         safe_action(sport_client.Dance1),
            "Dance2":         safe_action(sport_client.Dance2),

            "Front Flip":     safe_action(sport_client.FrontFlip),
            "Front Jump":     safe_action(sport_client.FrontJump),
            "Front Pounce":   safe_action(sport_client.FrontPounce),
            "Scrape":         safe_action(sport_client.Scrape),

            "Recovery Stand": recovery_stand,
            "Trot":           trot,
            "Run":            run,
            "Climb Stairs":   climb_stairs,
            "Down Stairs":    down_stairs,
        }

        backend_clients = {
            "audio":     DDSAudio(audio_client, vui_client),
            "video":     DDSVideo(video_client),
            "motion":    DDSMotion(sport_client),
            "telemetry": DDSTelemetry(self.communicator, self.idl_data_class),
            "led":       DDSLed(vui_client),
            "actions":   actions
        }

        return backend_clients



#                        # ---------------- SMART GAIT ACTIONS ----------------
#         def ensure_locomotion():
#             try:
#                 sport_client.StandUp()
#                 time.sleep(0.5)
#             except Exception as e:
#                 print(f"[WARN] ensure_locomotion failed: {e}")

#         def recovery_stand():
#             sport_client.RecoveryStand()

#         def trot():
#             ensure_locomotion()
#             sport_client.SwitchGait(1)

#         def run():
#             ensure_locomotion()
#             sport_client.SwitchGait(2)

#         def climb_stairs():
#             ensure_locomotion()
#             sport_client.FootRaiseHeight(0.12)
#             sport_client.SwitchGait(3)

#         def down_stairs():
#             ensure_locomotion()
#             sport_client.SwitchGait(4)

#         def stop():
#             sport_client.StopMove()

#         actions = {
# ######THOSE NOT WORKING COMMENTED OUT
#             # ---------------- BASIC ----------------
#             "Stand Up": sport_client.RecoveryStand,
#             "Stand Down": sport_client.StandDown,
#             "Stop": stop,
#             "Sit": sport_client.Sit,
#             #"Rise Sit": sport_client.RiseSit, 

#             # ---------------- INTERACTION ----------------
#             "Wave": sport_client.Hello,
#             "Hello": sport_client.Hello,
#             "Heart": sport_client.Heart,
#             "Stretch": sport_client.Stretch,

#             # ---------------- MOVEMENT / CONTROL ----------------
#             #"Trigger": sport_client.Trigger,
#             #"Trajectory": sport_client.TrajectoryFollow,

#             # ---------------- FUN / EXPRESSIVE ----------------
#             "Dance1": sport_client.Dance1,
#             "Dance2": sport_client.Dance2,
#             #"Wallow": sport_client.Wallow,
#             #"Wiggle Hips": sport_client.WiggleHips,

#             # ---------------- SPORT ACTIONS ----------------
#             "Front Flip": sport_client.FrontFlip,
#             "Front Jump": sport_client.FrontJump,
#             "Front Pounce": sport_client.FrontPounce,
#             "Scrape": sport_client.Scrape,

#             # # ---------------- ADVANCED MODE ----------------
#             # "Handstand": sport_client.HandStand,
#             # "Cross Step": sport_client.CrossStep,
#             # "One Side Step": sport_client.OneSideStep,
#             # "Bound": sport_client.Bound,

#             # # ---------------- AI MODE ----------------
#             # "Stand Out": sport_client.StandOut,

#             # ---------------- GAIT / LOCOMOTION ----------------
#             "Recovery Stand": recovery_stand,
#             "Trot": trot,
#             "Run": run,
#             "Climb Stairs": climb_stairs,
#             "Down Stairs": down_stairs,



#         }
 



class DDSAudio:
    def __init__(self, audio_client_var: AudioHubClient, vui_client_var: VuiClient):
        self.audio_client = audio_client_var
        self.vui_client = vui_client_var

    def play_sound(self, sound_name):
        self.audio_client.MegaphoneEnter()
        self.audio_client.MegaphoneUpload(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "sounds", sound_name)))
    
    def stop_sound(self):
        self.audio_client.MegaphoneExit()

    def change_volume(self, volume):
        self.vui_client.SetVolume(volume)


class DDSVideo:
    def __init__(self, client: VideoClient):
        self.client = client

    def stream_video(self):
        while True:
            code, data = self.client.GetImageSample()

            if code == 0:
                image_data = np.frombuffer(bytes(data), dtype=np.uint8)
                frame = cv2.imdecode(image_data, cv2.IMREAD_COLOR)

                _, buffer = cv2.imencode('.jpg', frame)
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')


class DDSMotion:
    def __init__(self, client: SportClient):
        self.client = client
        self.move_speed = 0.5
        self.turn_speed = 1.0

    def update_joystick(self, data):
        x, y, yaw = 0, 0, 0

        if data['stickId'] == 'stick1':
            x = -data['y'] * self.move_speed
            y = -data['x'] * self.move_speed

        if data['stickId'] == 'stick2':
            yaw = -data['x'] * self.turn_speed
            
        self.client.Move(x, y, yaw)


class DDSTelemetry:
    def __init__(self, communicator: DDSCommunicator, idl_data_class: IDLDataClass):
        self.dog_data = {}
        LowState_ = idl_data_class.get_data_class('LowState_')
        SportModeState_ = idl_data_class.get_data_class('SportModeState_')

        low_state_sub = communicator.ChannelSubscriber("rt/lowstate", LowState_)
        high_state_sub = communicator.ChannelSubscriber("rt/sportmodestate", SportModeState_)

        low_state_sub.Init(self.low_state_handler, 10)
        high_state_sub.Init(self.high_state_handler, 10)

    def low_state_handler(self, msg):
        self.dog_data.update({
            "voltage": format(msg.power_v, ".2f"),
            "current": format(msg.power_a, ".2f"),
            "avg temp": round((msg.temperature_ntc1 + msg.temperature_ntc2) / 2)
        })

    def high_state_handler(self, msg):
        self.dog_data.update({
            "velocity x": format(msg.velocity[0], ".2f"),
            "velocity y": format(msg.velocity[1], ".2f"),
            "velocity z": format(msg.velocity[2], ".2f"),
            "yaw spd": format(msg.yaw_speed, ".2f")
        })

    def stream_data(self):
        while True:
            data_array = [
                {'name': 'Voltage', 'value': self.dog_data.get('voltage', 'N/A')},
                {'name': 'Current', 'value': self.dog_data.get('current', 'N/A')},
                {'name': 'Average Temp', 'value': self.dog_data.get('avg temp', 'N/A')},
                {'name': 'Velocity X', 'value': self.dog_data.get('velocity x', 'N/A')},
                {'name': 'Velocity Y', 'value': self.dog_data.get('velocity y', 'N/A')},
                {'name': 'Velocity Z', 'value': self.dog_data.get('velocity z', 'N/A')},
                {'name': 'Yaw Speed', 'value': self.dog_data.get('yaw spd', 'N/A')}
            ]

            yield f"data: {json.dumps(data_array)}\n\n"
            time.sleep(0.1)




class DDSLed:
    def __init__(self, vui_client_var):
        self.vui_client = vui_client_var

    # ---------------------------
    # ON / OFF
    # ---------------------------
    def on(self):
        self.vui_client.SetSwitch(1)

    def off(self):
        self.vui_client.SetSwitch(0)
        self.vui_client.QuitLed(0)   # ensure LED effect stops

    # ---------------------------
    # BRIGHTNESS (0–10 as you want)
    # ---------------------------
    def set_brightness(self, brightness):
        self.vui_client.SetBrightness(brightness)

    # ---------------------------
    # COLOR
    # ---------------------------
    def set_color(self, color, time=300, flash_cycle=None):
        self.vui_client.SetLed(
            color=color,
            time=time,
            flash_cycle=flash_cycle
        )

    # ---------------------------
    # COMBINED CONTROL (useful)
    # ---------------------------
    def set_led(self, brightness=None, color=None, time=5):
        self.on()

        if brightness is not None:
            self.set_brightness(brightness)

        if color is not None:
            self.set_color(color, time=time)
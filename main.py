import gradio as gr
import threading
import rclpy
from rclpy.executors import MultiThreadedExecutor
from web_backend.data_stream import DataStream
import shutil
from config import CAMERA_TOPIC_NAME, INTERFACE, SHOW_LIDAR, SHOW_DESCRIPTION, SOUNDS_DIR, ROBOT, MODE, INTERFACE, ROSBRIDGE_IP , ROSBRIDGE_PORT

import os
os.makedirs(SOUNDS_DIR, exist_ok=True)

from web_frontend.index import get_index_page
from web_frontend.action import get_action_page
from web_frontend.dev import get_dev_page
from web_frontend.chatbot import get_chatbot_page





def list_sounds():
    return sorted(os.listdir(SOUNDS_DIR))

def refresh_list():
    return gr.update(choices=list_sounds())

def upload_file(file):
    if file is None:
        return "No file uploaded", refresh_list()

    filename = os.path.basename(file.name)
    dest = os.path.join(SOUNDS_DIR, filename)

    shutil.copy(file.name, dest)

    return f"Uploaded: {filename}", refresh_list()

def load_css_file(path):
    with open(path, "r") as f:
        return f.read()

# -------------------- Gradio UI --------------------------
def main():

    # --- ROS2 Init ---
    rclpy.init(args=None)
    
    #launcher = DataStream(LIDAR,COLOR_IMAGE,DEPTH_IMAGE,SEGMENTATION_IMAGE,DETECTION_IMAGE, CMD_VEL_PUB_TOPIC_NAME)
    launcher = DataStream(INTERFACE, CAMERA_TOPIC_NAME)
    def get_events():
        pass
        #return launcher.event_manager.get_events_log()
    
    executor = MultiThreadedExecutor()

    executor.add_node(launcher.image_subscriber)
    executor.add_node(launcher.rs_image_subscriber)
    executor.add_node(launcher.map_subscriber)
    executor.add_node(launcher.nav2_controller)
    executor.add_node(launcher.bm_subscriber)
    executor.add_node(launcher.audio_subscriber)

    #TODO executor.add_node(launcher.apriltag_inspector)

    
    #executor.add_node(launcher.lidar_subscriber)

    ros_thread = threading.Thread(target=executor.spin, daemon=True)
    ros_thread.start()

   # desc_thread = threading.Thread(target=launcher.update_description, daemon=True)
    pub_thread = threading.Thread(target=lambda: launcher.wirelesscontroller.pub_wirelesscontroller(0.0, 0.0, 0.0, 0.0, 0, 0), daemon=True)
    #safety_thread = threading.Thread(target=launcher.check_safety,daemon=True)
    
    
    #safety_thread.start()
    pub_thread.start()
    # ros_thread.start()
    # ros_lidar.start()
    # if SHOW_DESCRIPTION:
    #     desc_thread.start()

    # Spin ROS Camera Image subscriber in background -----------------------

    with gr.Blocks(
        title="MCP Web",
    ) as demo:
        
        gr.Markdown(f""" ROBOT `{ROBOT}` | ROSBRIDGE_ADDRESS `{ROSBRIDGE_IP}:{ROSBRIDGE_PORT}` | BACKEND_MODE `{MODE}` | INTERFACE `{INTERFACE}`""")

        with gr.Tabs():

            with gr.Tab("Main"):

                get_index_page(demo,launcher)


                event_timer = gr.Timer(1.0)
                event_timer.tick(
                    fn=get_events,
                    inputs=None,
                    outputs=None
                )

            with gr.Tab("Actions"):
                get_action_page(demo,launcher)


            with gr.Tab("Development"):

                get_dev_page()

            with gr.Tab("🤖 AI Assistant"):

                get_chatbot_page()

        demo.launch(
            server_name="0.0.0.0",
            server_port=7860,
            pwa=True,
            share=False,
            mcp_server=True,
            css=load_css_file("web_frontend/style.css")
        )


if __name__ == "__main__":
    main()

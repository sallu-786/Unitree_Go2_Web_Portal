import gradio as gr
import shutil
import os
from config import SOUNDS_DIR
os.makedirs(SOUNDS_DIR, exist_ok=True)


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

def get_action_page(demo,launcher):
    with gr.Row(elem_classes=["three-pane"]):

                        # ============================
                        # LEFT PANE — OPERATIONS
                        # ============================
                        with gr.Column(elem_classes=["left-pane"]):

                            gr.Markdown("### LED Control Panel")

                            with gr.Row():
                                # --- LEFT: FILE LIST ---
                                color_list = gr.Dropdown(
                                    choices=['white','red','yellow','blue','green','cyan','purple'],
                                    label="Available Colors"
                                )

                                # --- RIGHT: CONTROLS ---
                                with gr.Row():

                                    off_btn = gr.Button("⏹ Off")

                                brightness_slider = gr.Slider(
                                    minimum=0,
                                    maximum=10,
                                    step=1,
                                    value=5,
                                    label="Brightness (white only)"
                                )

                            def save_waypoint(name):
                                if not name:
                                    return "❌ Name required", gr.update()

                                x, y, yaw = launcher.get_robot_pose()

                                if x is None:
                                    return "❌ No pose data yet", gr.update()

                                data = launcher.load_data()
                                data[name] = {"x": x, "y": y, "yaw": yaw}
                                launcher.save_data(data)

                                return f"✅ Saved {name}", gr.update(choices=launcher.wp_choices())


                            def go_to_wp(name):
                                if not name:
                                    return "❌ Select waypoint"

                                data = launcher.load_data()
                                if name not in data:
                                    return "❌ Not found"

                                launcher.nav2_controller.go_to(data[name])
                                return f"🚀 Going to {name}"


                            def run_route():
                                data = launcher.load_data()
                                if not data:
                                    return "❌ No waypoints"

                                launcher.nav2_controller.run_route(list(data.values()))
                                return "🛣️ Running route"


                            def delete_wp(name):
                                data = launcher.load_data()
                                if name in data:
                                    del data[name]
                                    launcher.save_data(data)

                                return "🗑️ Deleted", gr.update(choices=launcher.wp_choices(), value=None)

                            wp_name = gr.Textbox(label="Waypoint Name")
                            save_btn = gr.Button("💾 Save Waypoint")

                            wp_dropdown = gr.Dropdown(choices=launcher.wp_choices(), label="Waypoints")

                            with gr.Row():
                                go_btn = gr.Button("▶ Go")
                                route_btn = gr.Button("▶▶ Full Route")
                                del_btn = gr.Button("🗑️")

                            wp_status = gr.Textbox(label="Status")

                            save_btn.click(save_waypoint, inputs=wp_name, outputs=[wp_status, wp_dropdown])
                            go_btn.click(go_to_wp, inputs=wp_dropdown, outputs=wp_status)
                            route_btn.click(run_route, outputs=wp_status)
                            del_btn.click(delete_wp, inputs=wp_dropdown, outputs=[wp_status, wp_dropdown])

                            demo.load(lambda: gr.update(choices=launcher.wp_choices()), outputs=wp_dropdown)



                            off_btn.click(launcher.led_subscriber.led_off, outputs=[])
                            color_list.change(launcher.led_subscriber.change_color, inputs=color_list, outputs=[])
                            brightness_slider.change(launcher.led_subscriber.change_brightness, inputs=brightness_slider, outputs=[])

                        
                                            # -------- CENTER PANE (SMALL CAMERAS + MAIN CAMERA) --------
                        with gr.Column(elem_classes=["center-pane"]):


                            # --- MAIN CAMERA ---
                            gr.Markdown("### 📸 Main Camera")
                            live_image = gr.Image(type="numpy", height=420)
                            live_text = gr.Textbox(label="Description", lines=3)

                            def live_feed_wrapper():
                                yield from launcher.live_cam_feed("color_image")

                            demo.load(
                                fn=live_feed_wrapper,
                                inputs=None,
                                outputs=[live_image, live_text]
                            )


                        with gr.Column(elem_classes=["right-pane"]):

                            gr.Markdown("### Audio Control Panel")

                            with gr.Row():
                                with gr.Column(scale=1):
                                    sound_list = gr.Dropdown(
                                        choices=list_sounds(),
                                        label="Available Sounds"
                                    )

                                with gr.Column(scale=1):
                                    with gr.Row():
                                        play_btn = gr.Button("▶ Play")
                                        stop_btn = gr.Button("⏹ Stop")

                            volume_slider = gr.Slider(
                                minimum=0,
                                maximum=10,
                                step=1,
                                value=2,
                                label="Volume (0–10)"
                            )


                            upload = gr.File(label="Upload Sound")

                                # 🎤 Mic (NEW)
                            mic = gr.Audio(
                                sources=["microphone"],
                                streaming=True,
                                type="numpy",
                                label="Live Mic"
                            )


                            # -------------------------
                            # Events
                        # -------------------------
                        play_btn.click(launcher.audio_subscriber.play_sound, inputs=sound_list, outputs=[])
                        stop_btn.click(launcher.audio_subscriber.stop_sound, outputs=[])

                        # Volume realtime
                        volume_slider.change(launcher.audio_subscriber.change_volume, inputs=volume_slider, outputs=[])

                        # Upload + refresh list
                        upload.change(upload_file, inputs=upload, outputs=[sound_list])

                        # 🎤 Mic streaming (NEW)
                        mic.stream(launcher.audio_subscriber.mic_stream, inputs=mic, outputs=[])
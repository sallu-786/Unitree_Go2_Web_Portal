# 🤖 MCP Web Portal — Unitree Go2 Robot Control Interface

A browser-based control and monitoring portal for the **Unitree Go2** robot dog, built with [Gradio](https://gradio.app/) and ROS2 keeping it 100% pythonic. The portal streams live camera feeds, displays sensor telemetry, provides remote navigation controls, supports autonomous waypoint missions, and integrates LLM-powered scene description.

---

## 📸 Overview

| Feature | Description |
|---|---|
| 🎥 Live Camera | Front-facing video stream + RealSense RGB/Depth + Yolo Object detection for both cameras|
| 🗺️ Map & Navigation | 2D Occupancy map with Nav2 goal setting |
| 🕹️ Remote Control | Wireless robot movement controller |
| 📡 Telemetry | Battery, pose, sport mode state, and sensor data |
| 🧠 AI Scene Description | LLM-based image analysis (OpenAI / Ollama) |
| 🔊 Audio / Sounds | Upload and Play audio files on the robot |
| 🔊 LED Controller | Change the color of Headlight and Brightness (White Only) |
| 📊 ROS Topic and Service Graph | Visual graph of all active topics and services |
| 🛠️ Development Tab | Diagnostic tools and dev utilities |
| 🌐 MCP Server Support| Integrated MCP Server that exposes all web topics and services to your Favourite LLM |

---

## 🗂️ Project Structure

```
.
├── main.py                   # App entry point — ROS2 init, Gradio launch
├── config.py                 # All settings (topics names, LLM config, Rosbridge connection settings, UI flags)
├── server.py                 # MCP Server that allows LLM Agent access to all of Ros2 topics and services
├── web_backend/
│    └── action_sub.py        # ROS2-style subscriber that allows using Go2 SportMode actions.
│    └── audio_sub.py         # Access Speaker of Go2
│    └── bm_status.py         # Battery, Motor and IMU (roll,pitch,yaw) status 
│    └── camera.py            # Access to Main front camera of Unitree Go2 
│    └── camera_rs.py         # Access to Main Realsense camera of Attached to Unitree Go2 (make sure Realsense ros2 pkg is installed on Go2) 
│   └── data_stream.py        # ROS2 subscribers, publishers, LLM logic, Map generator
├── web_frontend/
│   ├── index.py              # Main tab UI (camera, map, telemetry)
│   ├── action.py             # Actions tab UI (waypoints, missions)
│   ├── dev.py                # Development tab UI
│   └── style.css             # Custom CSS styles
├── data/
│   ├── yolo/best2.pt             # YOLO model weights
│   └── waypoints/waypoints.json  # Saved navigation waypoints
│   └── sounds/                   # Uploaded audio files for robot playback
```



## 🔧 Backend Customization

### Adding a New ROS2 Subscriber
1. Create a new subscriber class in `web_backend/` (follow the pattern of existing subscribers like `image_subscriber`).
2. Instantiate it inside `DataStream.__init__()` in `web_backend/data_stream.py`.
3. Register the node with the executor in `main.py`:
   ```python
   executor.add_node(launcher.your_new_subscriber)
   ```
4. Expose the data via a property or method on `DataStream` for the frontend to read.

### Adding a New UI Tab
1. Create a new file in `web_frontend/`, e.g., `web_frontend/my_tab.py`, and define a `get_my_tab_page(demo, launcher)` function using Gradio components.
2. Import and call it in `main.py` inside the `gr.Tabs()` block:
   ```python
   with gr.Tab("My Tab"):
       get_my_tab_page(demo, launcher)
   ```

### Changing the LLM Prompt
Edit `SYSTEM_PROMPT` and `LLM_PROMPT` in `config.py`:
```python
SYSTEM_PROMPT = "You are a robot assistant."
LLM_PROMPT = "Describe the scene and highlight any hazards."
```

### Adding a New LLM Model
Add your model to the `MODELS` dict using the LiteLLM model string format:
```python
MODELS = {
    "ollama": {
        "Gemma3": "ollama/gemma3:latest",
        "Llama3": "ollama/llama3:latest"   # ← new entry
    }
}
```

---

## 🚀 Installation

### Prerequisites
- **Ubuntu 22.04** (recommended)
- **ROS2 Humble** or later
- **Python 3.10+**
- **Unitree ROS2 SDK** — [unitree_ros2](https://github.com/unitreerobotics/unitree_ros2)
- **Nav2** (optional, for autonomous navigation)
- **Ollama** (optional, for local LLM inference)

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/mcp-web-portal.git
cd mcp-web-portal
```

### 2. Install Python Dependencies
```bash
pip install gradio rclpy opencv-python numpy pillow litellm python-dotenv
```

### 3. Source ROS2 and Unitree Setup
```bash
source /opt/ros/humble/setup.bash
source /home/your-user/unitree_ros2/setup.sh
```
> Update `UNITREE_ROS2_SETUP_SH_PATH` in `config.py` to match your actual path.

### 4. Configure Settings
Edit `config.py` to set your:
- Network interface (`INTERFACE`)
- ROS topic names
- LLM credentials
- Feature flags

### 5. (Optional) Set Up `.env` for API Keys
```bash
# .env
AZURE_API_KEY=your_key_here
```
Then in `config.py`:
```python
from dotenv import load_dotenv
import os
load_dotenv()
AZURE_API_KEY = os.getenv("AZURE_API_KEY")
```

### 6. Run the Portal
```bash
python main.py
```

The Gradio app will launch at **http://0.0.0.0:7860**. Open it in any browser on the same network.

---

## 🌐 Accessing the Portal

| Access Type | URL |
|---|---|
| Local (same machine) | `http://localhost:7860` |
| LAN (other devices) | `http://<robot-ip>:7860` |
| PWA (install on mobile) | Use browser's "Add to Home Screen" |

The app is configured as a **Progressive Web App (PWA)** — it can be installed on a phone or tablet for a native-app feel.

---

## 🐛 Troubleshooting

| Problem | Solution |
|---|---|
| No camera image | Check `CAMERA_TOPIC_NAME` matches your active ROS topic (`ros2 topic list`) |
| Map not loading | Verify `/map` topic is publishing and `MAP` config is correct |
| LLM not responding | Check `LLM_MODE`, credentials, and that Ollama is running if using local mode |
| Robot not moving | Confirm `CMD_VEL_PUB_TOPIC_NAME` and message type match your setup |
| Port 7860 in use | Change `server_port` in the `demo.launch()` call in `main.py` |
| ROS node errors | Ensure you have sourced both ROS2 and the Unitree setup scripts |

---

## 📄 License

This project is for internal/research use. Please respect the licenses of third-party dependencies including Gradio, ROS2, and the Unitree SDK.

---

## 🙏 Acknowledgements

- [Unitree Robotics](https://www.unitree.com/) — Go2 robot platform
- [Gradio](https://gradio.app/) — Web UI framework
- [Nav2](https://nav2.ros.org/) — ROS2 navigation stack
- [LiteLLM](https://github.com/BerriAI/litellm) — Unified LLM API layer
- [Ollama](https://ollama.com/) — Local LLM inference
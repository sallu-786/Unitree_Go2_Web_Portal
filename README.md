# 🤖 MCP Web Portal — Unitree Go2 Robot Control Interface

A browser-based control and monitoring portal for the **Unitree Go2** robot dog, built with [Gradio](https://gradio.app/) and ROS2 keeping it 100% pythonic. The portal streams live camera feeds, displays sensor telemetry, provides remote navigation controls, supports autonomous waypoint missions, and integrates LLM-powered scene description.


## Table of Contents


- [Feature Overview](#feature-overview)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Tech Stack](#tech-stack)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration Reference](#configuration-reference)
- [Running the MCP Portal](#running-the-mcp-portal)
- [MCP Server & LLM Agent Integration](#mcp-server--llm-agent-integration)
- [Accessing the Portal](#accessing-the-portal)
- [Extending the Project](#extending-the-project)
- [License & Acknowledgements](#license--acknowledgements)

---


## Feature Overview

| Feature | Description |
|---|---|
| 🎥 **Live Camera** | Front-facing video stream + Intel RealSense RGB/Depth feed, with YOLO object detection overlaid on either camera |
| 🗺️ **Map & Navigation** | 2D occupancy-grid map rendering with Nav2 goal-setting from the browser |
| 🕹️ **Remote Control** | Virtual joystick / directional controller for driving the robot over `WirelessController` messages |
| 📡 **Telemetry** | Live battery %, pose (x/y/yaw), sport-mode state, and IMU roll/pitch/yaw |
| 🧠 **AI Scene Description** | LLM-based image analysis of the camera feed (Azure OpenAI or local Ollama models via LiteLLM), with a configurable system prompt |
| 🔊 **Audio / Sounds** | Upload audio files and play them through the robot's onboard speaker |
| 💡 **LED Controller** | Adjust headlight color and brightness |
| 📊 **ROS Graph View** | Auto-generated visual graph of active ROS 2 topics, publishers, and subscribers |
| 🛠️ **Development Tab** | Diagnostic tools and dev utilities for debugging the ROS bridge/connections |
| 🌐 **MCP Server** | Exposes all portal-managed topics/services as MCP tools so an LLM agent can inspect and control the robot |
| 📍 **Waypoint Missions** | Save and replay autonomous navigation waypoints (`data/waypoints/waypoints.json`) |


---

## Architecture

```
┌─────────────────────┐        ROS 2 / DDS or WebRTC        ┌──────────────────┐
│   Unitree Go2 Robot   │◄────────────────────────────────►│  main.py (host)   │
│ (cameras, IMU, LIDAR,│        rosbridge (port 9090)        │  - ROS 2 executor │
│  sport-mode, motors)  │                                     │  - Gradio server  │
└─────────────────────┘                                     └────────┬─────────┘
                                                                        │
                       ┌────────────────────────────────────────────────┤
                       │                                                 │
              ┌────────▼────────┐                              ┌────────▼────────┐
              │  web_frontend/   │                              │   server.py      │
              │  Gradio tabs:    │                              │   MCP server      │
              │  index / action  │                              │   (tools → topics │
              │  / dev           │                              │   & services)     │
              └────────┬────────┘                              └────────┬────────┘
                       │                                                 │
              ┌────────▼─────────────────────────────────────┐         │
              │  web_backend/                                  │         │
              │  camera.py, camera_rs.py, bm_status.py,        │         │
              │  action_sub.py, audio_sub.py, data_stream.py   │         │
              │  (ROS 2 pub/subs, YOLO inference, map builder, │         │
              │   LiteLLM scene-description calls)             │         │
              └──────────────────────────────────────────────┘         │
                                                                          │
                                                          ┌───────────────▼───────────────┐
                                                          │  LLM Agent (ChatGPT / Ollama)  │
                                                          │  connects as an MCP client     │
                                                          └────────────────────────────────┘
```

The robot connects to the host machine via **rosbridge** (default `127.0.0.1:9090`), using either the **DDS** or **WebRTC** transport mode (`MODE` in `config.py`). All ROS 2 nodes are registered onto a shared executor in `main.py`, and their live data is surfaced to both the Gradio UI and the MCP server from the same `DataStream` object in `web_backend/data_stream.py`.

---

## Project Structure

```
.
├── main.py                    # App entry point — ROS2 init, node registration, Gradio launch
├── config.py                  # Central settings: topic names, LLM config, rosbridge connection, UI flags
├── server.py                  # MCP server exposing ROS2 topics/services as agent tools
├── test.py                    # Test/scratch script
├── pyproject.toml / uv.lock   # uv-managed dependency lockfile
├── requirements.txt           # Full pinned dependency list (ROS2, Gradio, ML, MCP stack)
│
├── web_backend/
│   ├── action_sub.py          # SportMode action interface (stand, sit, hello, dance, etc.)
│   ├── audio_sub.py           # Access to the Go2's onboard speaker
│   ├── bm_status.py           # Battery / motor / IMU (roll, pitch, yaw) status
│   ├── camera.py              # Main front camera access
│   ├── camera_rs.py           # RealSense RGB/Depth camera access (requires RealSense ROS2 pkg on the Go2)
│   └── data_stream.py         # Core hub: ROS2 subscribers/publishers, YOLO inference, LLM calls, map builder
│
├── web_frontend/
│   ├── index.py                # Main tab UI — camera, map, telemetry
│   ├── action.py                # Actions tab UI — waypoints, missions, sport commands
│   ├── dev.py                   # Development tab UI — diagnostics
│   └── style.css                # Custom CSS
│
├── backends/                  # Additional backend service modules
├── utils/                     # Shared helper utilities
│
├── data/
│   ├── yolo/best2.pt           # YOLO model weights used for object detection
│   ├── waypoints/waypoints.json# Saved navigation waypoints
│   └── sounds/                 # Uploaded audio files for robot playback
│
└── github_media/               # Screenshots / media used in repo documentation
```

---

## Tech Stack

Based on the project's pinned `requirements.txt`, the portal is built on:

- **Robotics / middleware:** ROS 2 (`rclpy`, `ros2cli` tooling), `rosbridge-suite` for the WebSocket bridge to the robot, `unitree_go`/`unitree_api`/`unitree_hg` message packages, and the [`unitree_sdk2_python`](https://github.com/unitreerobotics/unitree_sdk2_python) SDK (does not need seperate install, requirements.txt alread has it as an editable Git dependency)
- **Navigation:** `nav2-msgs`, `nav2-simple-commander`, `slam-toolbox`, `cartographer-ros-msgs` for occupancy-grid mapping and goal navigation. You may choose any code you like. I used following repo [`go2_slam_nav2`] (https://github.com/andy-zhuo-02/go2_ros2_toolbox)
- **Web UI:** `gradio` (v6.x) and `gradio_client` for the browser interface; `fastapi` / `starlette` / `uvicorn` underneath
- **Computer vision:** `opencv-python`, `ultralytics` (YOLO) for object detection, `torch` / `torchvision`
- **LLM / agent layer:** `litellm` (unified model API), `openai`, `ollama` (Python client), and `mcp` (the official Model Context Protocol SDK) for the agent-facing tool server
- **Audio:** `gTTS`, `pydub` for text-to-speech / audio handling
- **Real-time transport:** `aiortc`/`aioice`/`av` for optional WebRTC-based video/data channels
- **Misc:** `pandas`, `matplotlib`/`networkx` (for the ROS topic/service graph visualization), `redis`, `python-dotenv`

---

## Prerequisites

- **Ubuntu 22.04** (recommended)
- **ROS 2 Humble** or later
- **Python 3.10+**
- **Unitree ROS 2 SDK** — [unitreerobotics/unitree_ros2](https://github.com/unitreerobotics/unitree_ros2), installed and sourced
- **rosbridge_suite** (```bash
ros2 launch rosbridge_server rosbridge_websocket_launch.xml
```) (if you run it on laptop you can find it on `127.0.0.1:9090`)
- **Nav2** (optional — required only for autonomous waypoint navigation)
- **Intel RealSense ROS 2 package** installed on the Go2 (optional — required only for the RealSense RGB/Depth tab)
- **Ollama** (optional — for local LLM inference instead of Azure OpenAI)
- An NVIDIA GPU is not required, but the pinned requirements include CUDA-enabled `torch`/`nvidia-*` wheels for faster YOLO inference if one is available

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/sallu-786/Unitree_Go2_Web_Portal.git
cd Unitree_Go2_Web_Portal
```

### 2. Install Python dependencies

install from the pinned `requirements.txt` (note: this file includes ROS 2 Python packages, so it assumes a ROS 2 environment is already sourced/available):

```bash
pip install -r requirements.txt
```

### 3. Source ROS 2 and the Unitree setup script

```bash
source /opt/ros/humble/setup.bash
source /home/<your-user>/unitree_ros2/setup.sh
```

> Update `UNITREE_ROS2_SETUP_SH_PATH` in `config.py` to match the actual path on your machine.

### 4. Configure `config.py`

At minimum, review and set:

- `ROSBRIDGE_IP` / `ROSBRIDGE_PORT` — where rosbridge is running
- `MODE` — `"DDS"` or `"WEBRTC"`
- `INTERFACE` — your network interface for ROS 2 (`ip a` to find it)
- `ROBOT` — a friendly name for your robot
- Topic names (camera, cmd_vel, LIDAR, pose, odom, map, etc.) if they differ from your setup
- `UNITREE_ROS2_SETUP_SH_PATH` and `ROS_JS_LIB_PATH`

### 5. (Optional) Set up `.env` for API keys

Rather than hard-coding credentials in `config.py`, create a `.env` file:

```bash
# .env
AZURE_API_KEY=your_key_here
```

`config.py` already includes a warning that hard-coded keys are unsafe — load them via `python-dotenv` instead:

```python
from dotenv import load_dotenv
import os
load_dotenv()
AZURE_API_KEY = os.getenv("AZURE_API_KEY")
```

### 6. Run the portal

```bash
python main.py
```

The Gradio app launches at **`http://0.0.0.0:7860`** by default.

---

## Configuration Reference

All settings live in `config.py`. Key groups:

**Connection**
| Setting | Purpose |
|---|---|
| `ROSBRIDGE_IP` / `ROSBRIDGE_PORT` | Address of the rosbridge WebSocket server (default `127.0.0.1:9090`) |
| `MODE` | Transport mode — `"DDS"` or `"WEBRTC"` |
| `INTERFACE` | Network interface used for ROS 2 DDS traffic |
| `ROBOT` | Display name for the connected robot |

**LLM / Scene Description**
| Setting | Purpose |
|---|---|
| `LLM_MODE` | `"azure"` or `"ollama"` |
| `MODELS` | Dict mapping mode → friendly name → LiteLLM model string |
| `DEFAULT_MODEL` | Default model per mode |
| `AZURE_API_BASE` / `AZURE_OPENAI_DEPLOYMENT` / `AZURE_API_KEY` / `AZURE_API_VERSION` | Azure OpenAI credentials (use `.env`, not literals) |
| `OLLAMA_API_BASE` / `OLLAMA_API_KEY` | Local Ollama endpoint (default `http://localhost:11434`) |
| `SYSTEM_PROMPT` / `LLM_PROMPT` | Prompts used for periodic scene description; the shipped example is tuned for factory-floor PPE/hazard detection |
| `MCP_AGENT_PROMPT` | System prompt for the MCP-connected agent, instructing it to use tools for robot state/control and never claim success without a confirmed tool result |

**UI Feature Flags**
| Setting | Purpose |
|---|---|
| `SHOW_CAMERA` / `SHOW_TOPICS` / `SHOW_SERVICES` / `SHOW_CONTROLLER` / `SHOW_DESCRIPTION` / `SHOW_LIDAR` | Toggle individual UI panels on/off |
| `TTS_LANGUAGE` | Language code for text-to-speech (`"ja"` by default in the sample config) |
| `UPDATE_INTERVAL` | Seconds between periodic scene-description calls |
| `IMAGE_HEIGHT` / `IMAGE_WIDTH` | Camera stream display dimensions |
| `YOLO_MODE` | `"main"` for the front camera or `"rs"` for RealSense as the YOLO detection source |

**Paths**
| Setting | Purpose |
|---|---|
| `YOLO_MODEL` | Path to YOLO weights (`data/yolo/best2.pt`) |
| `SOUNDS_DIR` | Directory for uploaded playback audio |
| `WAYPOINT_FILE` | JSON file storing saved navigation waypoints |
| `UNITREE_ROS2_SETUP_SH_PATH` | Path to the Unitree ROS 2 `setup.sh` |
| `ROS_JS_LIB_PATH` | Path to the JS library used for browser-side map/nav rendering |

**Topic Names** — all remappable to match your robot's actual topic names: `CAMERA_TOPIC_NAME`, `REALSENSE_CAMERA_COLOR`, `REALSENSE_CAMERA_DEPTH`, `CMD_VEL_PUB_TOPIC_NAME` (+ `_TYPE`), `LIDAR` (+ `LIDAR_MAX_POINTS`), `POSE` (+ `POSE_HEADER_FRAME_ID`), `ODOM`, `MAP`, `SPORTS`, `LFLOWCMD`.

**ROS Graph Styling** — `TOPIC_COLOR`, `PUBLISHER_COLOR`, `SUBSCRIBER_COLOR`, `NODE_SIZE`, `TOPIC_SIZE`, `PLOT_WIDTH`, `PLOT_HEIGHT` control the appearance of the topic/service graph shown in the UI.

---

## Running the MCP Portal

```bash
python main.py
```

This will:
1. Initialize `rclpy`, instantiate all ROS 2 subscriber/publisher nodes defined in `web_backend/`, and register them on a shared executor.
2. Launch the Gradio app with tabs for the main dashboard, actions/waypoints, and development diagnostics.
3. Start the background loop that periodically grabs a camera frame, runs it through the configured LLM, and updates the on-screen scene description.

---

## MCP Server & LLM Agent Integration

`server.py` starts an MCP server that mirrors the robot's ROS 2 surface as callable tools — battery/pose/telemetry reads, topic/service introspection, and movement/action commands. Any MCP-compatible client (a custom agent script, an IDE assistant, or a chat UI wired up with an MCP connector) can attach to it and:

- List and inspect active ROS 2 topics and services
- Read live telemetry (battery, pose, sport-mode state, sensors)
- Issue movement or action commands through the exposed tools
- Get grounded, tool-verified answers rather than the model guessing at robot state

The `MCP_AGENT_PROMPT` in `config.py` explicitly instructs the connected agent to rely on tool calls for anything robot-related and to never report success unless a tool call actually confirms it — useful guardrails when letting an LLM drive a physical robot.

To customize which model powers the natural-language side of the agent, add entries to `MODELS` in `config.py` using [LiteLLM's model string format](https://docs.litellm.ai/docs/providers), e.g.:

```python
MODELS = {
    "ollama": {
        "Gemma3": "ollama/gemma3:latest",
        "Llama3": "ollama/llama3:latest",   # ← new entry
    }
}
```

---

## Accessing the Portal

| Access Type | URL |
|---|---|
| Local (same machine) | `http://localhost:7860` |
| LAN (other devices) | `http://<robot-host-ip>:7860` |
| PWA (install on mobile) | Open in a mobile browser → "Add to Home Screen" |

The portal is configured as a **Progressive Web App**, so it can be installed on a phone or tablet for a near-native experience — handy for field use where you don't want a full desktop browser open.

---

## Extending the Project

**Add a new ROS 2 subscriber**
1. Create a new subscriber class in `web_backend/`, following the pattern of an existing one (e.g. the camera subscribers).
2. Instantiate it inside `DataStream.__init__()` in `web_backend/data_stream.py`.
3. Register the node with the executor in `main.py`:
   ```python
   executor.add_node(launcher.your_new_subscriber)
   ```
4. Expose the data via a property or method on `DataStream` so the frontend can read it.

**Add a new UI tab**
1. Create `web_frontend/my_tab.py` and define a `get_my_tab_page(demo, launcher)` function using Gradio components.
2. Wire it into `main.py` inside the `gr.Tabs()` block:
   ```python
   with gr.Tab("My Tab"):
       get_my_tab_page(demo, launcher)
   ```

**Change the LLM scene-description prompt**

Edit `SYSTEM_PROMPT` and `LLM_PROMPT` in `config.py`:

```python
SYSTEM_PROMPT = "You are a robot assistant."
LLM_PROMPT = "Describe the scene and highlight any hazards."
```

**Add a new LLM model** — add an entry to the `MODELS` dict as shown above in the MCP section.

---


## License & Acknowledgements

This project is intended for internal/research use. Please respect the licenses of its third-party dependencies, including Gradio, ROS 2, the Unitree SDK, and the MCP SDK. See the repository's [`LICENSE`](https://github.com/sallu-786/Unitree_Go2_Web_Portal/blob/main/LICENSE) file for details.

**Built on top of:**
- [Unitree Robotics](https://www.unitree.com/) — Go2 robot platform
- [Gradio](https://gradio.app/) — Web UI framework
- [Nav2](https://nav2.ros.org/) — ROS 2 navigation stack
- [LiteLLM](https://github.com/BerriAI/litellm) — Unified LLM API layer
- [Ollama](https://ollama.com/) — Local LLM inference
- [Model Context Protocol](https://modelcontextprotocol.io/) — Agent/tool integration standard
- [Ultralytics YOLO](https://github.com/ultralytics/ultralytics) — Object detection

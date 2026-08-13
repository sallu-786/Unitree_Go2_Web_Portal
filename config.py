# ROS bridge connection settings
ROSBRIDGE_IP = "127.0.0.1"  # Default=localhost. Replace with your IP of device hosting rosbridge service if different.
ROSBRIDGE_PORT = 9090  # default=9090.
MODE="DDS" # DDS or WEBRTC
INTERFACE="enp132s0" #  enp132s0, wlp129s0f0 interface used for Ros2..in cmd type ip a and check your interface
ROBOT="Alpha" # Add your robot name 


LLM_MODE = "ollama"   # "azure" or "ollama"

#Add or remove your LLM models here
MODELS = {
    "azure": {
        "ChatGPT-4o": "azure/azure_openai_app_4o"
    },
    "ollama": {
        "llama3": "ollama_chat/llama3:latest",
        "qwen": "ollama_chat/qwen3:8b",
        "muse": "ollama_chat/muse-glimmer:latest",

    }
}

#Set default model for each mode
DEFAULT_MODEL = {
    "azure": "ChatGPT-4o",
    "ollama": "muse",
    
}

# AZURE CONFIG : WARNING::::THIS MAY NOT be safe, make a .env file and import API key from there)
AZURE_API_BASE = ""
AZURE_OPENAI_DEPLOYMENT = ""  
AZURE_API_KEY = ""
AZURE_API_VERSION=""

# OLLAMA CONFIG
OLLAMA_API_BASE = "http://localhost:11434"
OLLAMA_API_KEY = "local"

# PROMPTS
SYSTEM_PROMPT = "You are Unitree Go2 Camera image analyzer describing the scene."
LLM_PROMPT="What do you see? Tell me v briefly. If you are in factory enviorment then Detect (if any) people in image are wearing helmet/cap, \
        glasses, and Toyota Boshoku jacket(beige colored )  \
        Also tell user of some warning signs or some dangerous situation if any. Use japanese...Let me give you an example  \
        工場のような環境ですね。ヘルメットと結核対策用のキャップはかぶっているのに、眼鏡をかけていない人がいます。床には配線が敷かれていて、つまずく恐れがあります。"



MCP_AGENT_PROMPT="""
You are an intelligent ROS2 robot assistant.

You have access to MCP tools that can inspect and control a ROS2 robot.

Use MCP tools whenever the user asks for information about the robot,
ROS topics, services, network, sensors, or robot state.

For robot control commands, use the appropriate MCP tool.

Be concise and explain what you did.

Never claim that an action succeeded unless the MCP tool actually
returned a successful result.

If tooling fails explain what happened briefly and accurately..always keep user engaged and inform with correct information
"""




#----------------------------------------------------------------------
SHOW_CAMERA=True
SHOW_TOPICS=True
SHOW_SERVICES=True
SHOW_CONTROLLER=True
SHOW_DESCRIPTION=True
SHOW_LIDAR=False
TTS_LANGUAGE="ja" #en
UPDATE_INTERVAL=12
IMAGE_HEIGHT=580
IMAGE_WIDTH=740
YOLO_MODE="main" #IF main camera use "main" if realsense camera use "rs" 



# PATH TO DIRECTORIES--------------------------------------------------

YOLO_MODEL="data/yolo/best2.pt"   
SOUNDS_DIR = "data/sounds"
WAYPOINT_FILE = "data/waypoints/waypoints.json"
UNITREE_ROS2_SETUP_SH_PATH = "/home/sallu/unitree_ros2/setup.sh" #install unitree ros2 and give its path here
ROS_JS_LIB_PATH = "/home/sallu/GO2/suleman/web_portal_github_beta/ros"#Path to Javascript Library for map and navigation in browser



#------------------------------TOPIC NAMES--------------------------------


CAMERA_TOPIC_NAME="/frontvideostream"
REALSENSE_CAMERA_COLOR="/camera/camera/color/image_raw"
REALSENSE_CAMERA_DEPTH="/camera/camera/depth/image_rect_raw"

CMD_VEL_PUB_TOPIC_NAME="/wirelesscontroller"
CMD_VEL_PUB_TOPIC_TYPE="unitree_go/msg/WirelessController"


LIDAR="/utlidar/cloud"
LIDAR_MAX_POINTS=300_000 #to reduce computation load

POSE="/utlidar/robot_pose"
POSE_HEADER_FRAME_ID="map"
ODOM="/odom" #/utlidar/robot_odom
MAP="/map" 
SPORTS="/sportmodestate"
LFLOWCMD="/lf/lowstate"


#-----------------------------------Topics and Services Graph------------------
TOPIC_COLOR="orange"
PUBLISHER_COLOR="lightblue"
SUBSCRIBER_COLOR="lightgreen"
NODE_SIZE=2000
TOPIC_SIZE=1000
PLOT_WIDTH=16
PLOT_HEIGHT=12
import json
from server import (
    get_list_topics, get_topic_type, get_topic_message, get_topic_publishers, get_topic_subscribers,get_echo_topic_once)

from utils.topics import (list_topics,topic_type, topic_message, topic_publishers, topic_subscribers, echo_topic_once)
import matplotlib.patches as mpatches
from config import TOPIC_COLOR, PUBLISHER_COLOR, SUBSCRIBER_COLOR, NODE_SIZE, TOPIC_SIZE, PLOT_WIDTH,PLOT_HEIGHT
import matplotlib.pyplot as plt
import networkx as nx
import tempfile
import json
import math 
from mcp.server.fastmcp import FastMCP
from utils.websocket_manager import WebSocketManager
from config import ROSBRIDGE_IP, ROSBRIDGE_PORT 


# Initialize MCP server and WebSocket manager
mcp = FastMCP("ros-mcp-server")
ws_manager = WebSocketManager(
    ROSBRIDGE_IP, ROSBRIDGE_PORT, default_timeout=5.0)  # Increased default timeout for ROS operations

def quat_to_euler(x, y, z, w):
    # roll (x-axis rotation)
    t0 = 2.0 * (w * x + y * z)
    t1 = 1.0 - 2.0 * (x * x + y * y)
    roll = math.atan2(t0, t1)

    # pitch (y-axis rotation)
    t2 = 2.0 * (w * y - z * x)
    t2 = max(min(t2, 1.0), -1.0)
    pitch = math.asin(t2)

    # yaw (z-axis rotation)
    t3 = 2.0 * (w * z + x * y)
    t4 = 1.0 - 2.0 * (y * y + z * z)
    yaw = math.atan2(t3, t4)

    return roll, pitch, yaw

# ---------- JSON Pretty Formatter ----------
def pretty_format(data) -> str:
    """Format dict/list objects in a readable way"""
    try:
        return json.dumps(data, indent=8, ensure_ascii=False)
    except Exception:
        return str(data)
    
def parse_json(result_str):
    """Convert pretty_format() output back into Python objects if needed"""
    try:
        return json.loads(result_str)
    except Exception:
        return []
    
def extract_nodes(data, key):
    """Extract list of node names from topic dict"""
    if not isinstance(data, dict):
        return []
    return data.get(key, [])  # key = "publishers" or "subscribers"
    
def view_list_topics():
    try:
        result = list_topics(ws_manager)
        #result = get_list_topics()
        return result.get("topics", [])
    except Exception as e:
        print(f"Error fetching topics: {e}")
        return []

def get_topic_operations() -> list[str]:
    return ["View Type", "View Message Definition", "View Publishers", "View Subscribers", "Echo"]

def execute_topic_operation(topic: str, operation: str):
    if not topic:
        return "Please select a topic."
    if not operation:
        return "Please select an operation."

    # try:
    if operation == "View Type":
        result = topic_type(ws_manager, topic)
    elif operation == "View Message Definition":
        topic_typ = topic_type(ws_manager,topic).get("type", "")
        if not topic_typ:
            return f"Could not resolve message type for {topic}"
        result = topic_message(ws_manager, topic_typ)
    elif operation == "View Publishers":
        result = topic_publishers(ws_manager, topic)
    elif operation == "View Subscribers":
        result = topic_subscribers(ws_manager, topic)
    elif operation =="Echo":
        topic_typ = topic_type(ws_manager,topic).get("type", "")
        if not topic_typ:
            return f"Could not resolve message type for {topic}"
        result = echo_topic_once(ws_manager,topic,topic_typ)
    else:
        return "Unknown operation."

    return pretty_format(result)
    # except Exception as e:
    #     return f"Error executing {operation} on {topic}: {e}"
    
def get_pose(topic: str):
    result = parse_json(execute_topic_operation(topic, "Echo"))

    pose = result.get("pose")
    if not pose:
        return None, None
    else:
        pos = pose.get("position") or {}
        ori = pose.get("orientation") or {}

        position = (
            f"x (fwd+/back-):     {pos.get('x', 0):.2f}\n"
            f"y (left+/right-):   {pos.get('y', 0):.2f}\n"
            f"z (up+/down-):      {pos.get('z', 0):.2f}"
        )

        x=ori.get('x', 0)
        y=ori.get('y', 0)
        z=ori.get('z', 0)
        w=ori.get('w', 0)
        roll,pitch,yaw = quat_to_euler(x,y,z,w)
        euler_orientation = (
            f"roll (left/right):     {roll:.2f}\n"
            f"pitch (up/down):       {pitch:.2f}\n"
            f"yaw (left/right rotate):    {yaw:.2f}"            
         )

        return position, euler_orientation

def get_velocity(topic: str):
    result = parse_json(execute_topic_operation(topic, "Echo"))
    twist_1 = result.get("twist")
    if not twist_1:
        return None, None
    else:
        twist_2=twist_1.get("twist")
        lin_vel = twist_2.get("linear") or {}
        ang_vel = twist_2.get("angular") or {}

        linear_vel = (
            f"x (fwd+/back-):     {lin_vel.get('x', 0):.2f}\n"
            f"y (left+/right-):   {lin_vel.get('y', 0):.2f}\n"
            f"z (up+/down-):      {lin_vel.get('z', 0):.2f}"
        )
        #rad/sec
        angular_vel = (
            f"roll (left up+/right up- ):     {ang_vel.get('x', 0):.2f}\n"
            f"pitch(nose up+/nose down- ):   {ang_vel.get('y', 0):.2f}\n"
            f"yaw (ccw+/cw- rotation):      {ang_vel.get('z', 0):.2f}"
        )



        return linear_vel, angular_vel


def build_ros_graph_snapshot(selected_topics=None):
    G = nx.DiGraph()
    topics = selected_topics if selected_topics else view_list_topics()
    
    pub_y, topic_y, sub_y = 0, 0, 0
    y_step = 1.5
    pos = {}

    for topic in topics:
        # --- Publishers ---
        pub_data = parse_json(execute_topic_operation(topic, "View Publishers"))
        pubs = extract_nodes(pub_data, "publishers")
        for pub in pubs:
            G.add_node(pub, color=PUBLISHER_COLOR, node_size=NODE_SIZE)
            G.add_edge(pub, topic)
            pos[pub] = (-2, pub_y)
            pub_y += y_step

        # --- Topic Node ---
        G.add_node(topic, color=TOPIC_COLOR, node_size=TOPIC_SIZE)
        pos[topic] = (0, topic_y)
        topic_y += y_step

        # --- Subscribers ---
        sub_data = parse_json(execute_topic_operation(topic, "View Subscribers"))
        subs = extract_nodes(sub_data, "subscribers")
        for sub in subs:
            G.add_node(sub, color=SUBSCRIBER_COLOR, node_size=NODE_SIZE)
            G.add_edge(topic, sub)
            pos[sub] = (2, sub_y)
            sub_y += y_step

    # Draw graph
    plt.figure(figsize=(PLOT_WIDTH, PLOT_HEIGHT))
    node_colors = [G.nodes[n].get("color", "blue") for n in G.nodes()]
    node_sizes = [G.nodes[n].get("node_size", NODE_SIZE) for n in G.nodes()]

    nx.draw(
        G, pos, with_labels=True,
        node_size=node_sizes,
        node_color=node_colors,
        font_size=12,
        font_weight="bold",
        arrows=True,
        arrowsize=5,
        width=1.0,
        connectionstyle='arc3,rad=0.1'
    )

    # Legend

    topic_patch = mpatches.Patch(color=TOPIC_COLOR, label='Topic')
    publisher_patch = mpatches.Patch(color=PUBLISHER_COLOR, label='Publisher Node')
    subscriber_patch = mpatches.Patch(color=SUBSCRIBER_COLOR, label='Subscriber Node')
    plt.legend(handles=[topic_patch, publisher_patch, subscriber_patch], loc='upper right', fontsize=6)

    tmp_png = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    plt.savefig(tmp_png.name, format="png", bbox_inches="tight")
    plt.close()
    return tmp_png.name

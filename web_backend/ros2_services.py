import json
# from server import (
#     get_list_services, get_service_type, get_service_detail, get_service_nodes)
from utils.services import (list_services, service_type, service_detail, service_nodes)
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import tempfile
# from utils.services import list_services, service_type, service_detail, service_nodes
from mcp.server.fastmcp import FastMCP
from utils.websocket_manager import WebSocketManager
from config import ROSBRIDGE_IP, ROSBRIDGE_PORT 


# Initialize MCP server and WebSocket manager
mcp = FastMCP("ros-mcp-server")
ws_manager = WebSocketManager(
    ROSBRIDGE_IP, ROSBRIDGE_PORT, default_timeout=5.0)  # Increased default timeout for ROS operations

# ---------- JSON Pretty Formatter ----------
def pretty_format(data) -> str:
    """Format dict/list objects in a readable way"""
    try:
        return json.dumps(data, indent=8, ensure_ascii=False)
    except Exception:
        return str(data)

def view_list_services():
    try:
        result = list_services(ws_manager)
        return result.get("services", [])
    except Exception as e:
        print(f"Error fetching services: {e}")
        return []

def get_service_operations() -> list[str]:
    return [
        "View Type",
        "View Detail (req/resp structures)",
        "View Providers",
        #"Interface Show"
    ]

def execute_service_operation(service: str, operation: str):
    if not service and operation != "View All Services Detail":
        return "Please select a service."
    if not operation:
        return "Please select an operation."

    try:
        if operation == "View Type":
            result = service_type(ws_manager, service)
        elif operation == "View Detail (req/resp structures)":
            serv_type = service_type(ws_manager,service).get("type", "")
            if not serv_type:
                return f"Could not resolve type for {service}"
            result = service_detail(ws_manager, serv_type)
        elif operation == "View Providers":
            result = service_nodes(ws_manager,service)
        else:
            return "Unknown operation."

        return pretty_format(result)
    except Exception as e:
        return f"Error executing {operation} on {service}: {e}"
    

def build_service_graph_snapshot(selected_services=None, show_types=True):
    G = nx.DiGraph()
    services = selected_services if selected_services else view_list_services()

    # Positioning offsets
    provider_y, service_y, type_y = 0, 0, 0
    y_step = 1.5
    pos = {}

    for service in services:
        # --- Providers ---
        try:
            providers_data = execute_service_operation(service, "View Providers")
            providers_json = json.loads(providers_data)
            providers = providers_json.get("nodes", [])
        except Exception:
            providers = []

        for provider in providers:
            G.add_node(provider, color="lightblue", node_size=2000)
            G.add_edge(provider, service)
            pos[provider] = (-2, provider_y)
            provider_y += y_step

        # --- Service Node ---
        G.add_node(service, color="orange", node_size=1000)
        pos[service] = (0, service_y)
        service_y += y_step

        # --- Service Type ---
        if show_types:
            try:
                type_data = execute_service_operation(service, "View Type")
                type_json = json.loads(type_data)
                serv_type = type_json.get("type", "")
                if serv_type:
                    G.add_node(serv_type, color="lightgreen", node_size=1000)
                    G.add_edge(service, serv_type)

                    # Spread types diagonally (avoids stacking near legend)
                    pos[serv_type] = (3, type_y - 0.5 * service_y)
                    type_y += y_step
            except Exception:
                pass

    # --- Draw Graph ---
    plt.figure(figsize=(12, 8))
    node_colors = [G.nodes[n].get("color", "lightblue") for n in G.nodes()]
    node_sizes = [G.nodes[n].get("node_size", 1000) for n in G.nodes()]

    nx.draw(
        G, pos, with_labels=True,
        node_size=node_sizes,
        node_color=node_colors,
        font_size=10,
        font_weight="bold",
        arrows=True,
        arrowsize=6,
        width=1.0,
        connectionstyle='arc3,rad=0.1'
    )

    # --- Legend outside plot (avoids overlap) ---
    service_patch = mpatches.Patch(color='orange', label='Service')
    provider_patch = mpatches.Patch(color='lightblue', label='Provider Node')
    type_patch = mpatches.Patch(color='lightgreen', label='Service Type')
    plt.legend(
        handles=[service_patch, provider_patch, type_patch],
        loc='center left',
        bbox_to_anchor=(1, 0.5),
        fontsize=12
    )

    tmp_png = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    plt.savefig(tmp_png.name, format="png", bbox_inches="tight")
    plt.close()
    return tmp_png.name

import gradio as gr
from web_backend.ros2_topics import (
    view_list_topics, get_topic_operations, execute_topic_operation, build_ros_graph_snapshot)  #get_pose, get_velocity
from web_backend.ros2_services import (
    view_list_services, get_service_operations, execute_service_operation, build_service_graph_snapshot)


def get_dev_page():
    with gr.Row():

                    # ============================
                    # LEFT PANE — OPERATIONS
                    # ============================
                    with gr.Column(scale=1):

                        gr.Markdown("## ⚙️ Operations")

                        mode_selector = gr.Radio(
                            ["Topics", "Services"],
                            label="Select Mode",
                            value="Topics"
                        )

                        # -------- TOPIC OPS --------
                        topic_dropdown = gr.Dropdown(
                            choices=view_list_topics(),
                            label="Select Topic",
                            visible=True
                        )
                        topic_op_dropdown = gr.Dropdown(
                            choices=get_topic_operations(),
                            label="Operation",
                            visible=True
                        )
                        topic_result = gr.Textbox(
                            label="Topic Result",
                            lines=6,
                            interactive=False,
                            visible=True
                        )

                        # -------- SERVICE OPS --------
                        service_dropdown = gr.Dropdown(
                            choices=view_list_services(),
                            label="Select Service",
                            visible=False
                        )
                        service_op_dropdown = gr.Dropdown(
                            choices=get_service_operations(),
                            label="Operation",
                            visible=False
                        )
                        service_result = gr.Textbox(
                            label="Service Result",
                            lines=8,
                            interactive=False,
                            visible=False
                        )

                    # ============================
                    # RIGHT PANE — VISUALIZERS
                    # ============================
                    with gr.Column(scale=1):

                        gr.Markdown("## 📊 Visualizer")

                        # -------- TOPICS VISUALIZER --------
                        with gr.Group(visible=True) as topics_viz:
                            gr.Markdown("### 📡 Topics Graph")
                            topic_graph = gr.Image(type="filepath", label="Topics Graph Snapshot")

                            all_topics = view_list_topics()
                            topic_select = gr.Dropdown(
                                choices=all_topics,
                                label="Topics to Visualize",
                                value=all_topics,
                                multiselect=True
                            )
                            refresh_topics = gr.Button("Build Topic Graph")

                            refresh_topics.click(
                                build_ros_graph_snapshot,
                                topic_select,
                                topic_graph
                            )

                        # -------- SERVICES VISUALIZER --------
                        with gr.Group(visible=False) as services_viz:
                            gr.Markdown("### 🔧 Services Graph")
                            service_graph = gr.Image(type="filepath", label="Services Graph Snapshot")

                            all_services = view_list_services()
                            service_select = gr.Dropdown(
                                choices=all_services,
                                label="Services to Visualize",
                                value=all_services,
                                multiselect=True
                            )
                            refresh_services = gr.Button("Build Service Graph")

                            refresh_services.click(
                                build_service_graph_snapshot,
                                service_select,
                                service_graph
                            )

                    # ============================
                    # MODE SWITCH LOGIC
                    # ============================
                    def switch_mode(mode):
                        return (
                            # topic ops
                            gr.update(visible=mode == "Topics"),
                            gr.update(visible=mode == "Topics"),
                            gr.update(visible=mode == "Topics"),

                            # service ops
                            gr.update(visible=mode == "Services"),
                            gr.update(visible=mode == "Services"),
                            gr.update(visible=mode == "Services"),

                            # visualizers
                            gr.update(visible=mode == "Topics"),
                            gr.update(visible=mode == "Services"),
                        )

                    mode_selector.change(
                        switch_mode,
                        inputs=mode_selector,
                        outputs=[
                            topic_dropdown, topic_op_dropdown, topic_result,
                            service_dropdown, service_op_dropdown, service_result,
                            topics_viz, services_viz
                        ]
                    )

                    # ============================
                    # EXECUTION HOOKS
                    # ============================
                    topic_dropdown.change(
                        execute_topic_operation,
                        [topic_dropdown, topic_op_dropdown],
                        topic_result
                    )
                    topic_op_dropdown.change(
                        execute_topic_operation,
                        [topic_dropdown, topic_op_dropdown],
                        topic_result
                    )

                    service_dropdown.change(
                        execute_service_operation,
                        [service_dropdown, service_op_dropdown],
                        service_result
                    )
                    service_op_dropdown.change(
                        execute_service_operation,
                        [service_dropdown, service_op_dropdown],
                        service_result
                    )
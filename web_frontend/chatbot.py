import gradio as gr

from web_backend.mcp_agent import stream_agent


async def chatbot_response(user_message, history):

    if not user_message or not user_message.strip():
        yield history, "", "Please enter a command."
        return

    history = history or []

    # Add user message
    history.append({
        "role": "user",
        "content": user_message
    })

    # Add assistant message
    history.append({
        "role": "assistant",
        "content": ""
    })

    thinking_text = ""
    assistant_text = ""

    yield history, "", "Connecting to Go2 MCP..."

    try:

        async for event in stream_agent(user_message):

            event_type = event.get("type")

            # -----------------------------------------
            # FULL THINKING
            # -----------------------------------------

            if event_type == "thinking":

                thinking_text += event.get("text", "")

                history[-1]["content"] = (
                    f"<small>"
                    f"🤔 **Thinking:**\n\n"
                    f"{thinking_text}"
                    f"</small>"
                )

                yield (
                    history,
                    "",
                    "🤔 Thinking..."
                )

            # -----------------------------------------
            # NORMAL ANSWER
            # -----------------------------------------

            elif event_type == "content":

                assistant_text += event.get("text", "")

                history[-1]["content"] = (
                    f"<small>"
                    f"🤔 **Thinking:**\n\n"
                    f"{thinking_text}"
                    f"</small>\n\n"
                    f"---\n\n"
                    f"{assistant_text}"
                )

                yield (
                    history,
                    "",
                    "💬 Responding..."
                )

            # -----------------------------------------
            # MCP TOOL CALL
            # -----------------------------------------

            elif event_type == "tool_call":

                tool_name = event.get(
                    "name",
                    "unknown"
                )

                yield (
                    history,
                    "",
                    f"🔧 Using ROS2 tool: {tool_name}"
                )

            # -----------------------------------------
            # MCP TOOL RESULT
            # -----------------------------------------

            elif event_type == "tool_result":

                yield (
                    history,
                    "",
                    "✅ ROS2 tool completed. Processing result..."
                )

        yield (
            history,
            "",
            "Ready"
        )

    except Exception as e:

        error_message = f"❌ Agent error: {e}"

        history[-1]["content"] = error_message

        yield (
            history,
            "",
            error_message
        )


def clear_chat():
    return [], "", "Ready"


def get_chatbot_page():
    """
    Creates the ROS2 MCP chatbot tab.
    """

    gr.HTML(
        """
        <style>
        #go2-header {
            display: flex; align-items: baseline; gap: 10px;
            padding: 4px 2px 14px 2px;
        }
        #go2-header h1 {
            font-family: 'IBM Plex Mono', 'JetBrains Mono', monospace;
            font-size: 1.4rem; letter-spacing: 0.02em; margin: 0;
            color: #e6f6ff;
        }
        #go2-header .tag {
            font-family: 'IBM Plex Mono', monospace;
            font-size: 0.72rem; letter-spacing: 0.12em; text-transform: uppercase;
            color: #5fd4ff; border: 1px solid #1c4a5c; border-radius: 4px;
            padding: 2px 7px; opacity: 0.85;
        }
        #go2-sub { color: #8aa0ab; font-size: 0.92rem; margin: -6px 0 14px 2px; }

        #go2-chat { border: 1px solid #1c2b33 !important; border-radius: 10px !important; }
        #go2-chat .message.user { background: #123047 !important; border-radius: 10px !important; }
        #go2-chat .message.bot {
            background: #10181d !important; border-left: 2px solid #5fd4ff !important;
            border-radius: 4px 10px 10px 10px !important;
        }

        #go2-input textarea {
            font-family: 'IBM Plex Mono', monospace !important;
            border-radius: 8px !important;
        }
        #go2-send button, #go2-send {
            border-radius: 8px !important;
            box-shadow: 0 0 0 1px #1c4a5c inset;
        }

        #go2-status textarea {
            font-family: 'IBM Plex Mono', monospace !important;
            font-size: 0.85rem !important;
            background: #0c1418 !important;
            border: 1px solid #1c2b33 !important;
            color: #5fd4ff !important;
        }
        #go2-status label { letter-spacing: 0.08em; text-transform: uppercase; font-size: 0.72rem !important; }

        #go2-examples {
            border: 1px solid #1c2b33; border-radius: 10px;
            padding: 10px 14px; margin-top: 4px; background: #0c1418;
        }
        #go2-examples h3 {
            font-family: 'IBM Plex Mono', monospace; font-size: 0.75rem;
            letter-spacing: 0.12em; text-transform: uppercase; color: #5fd4ff;
            margin: 2px 0 8px 0;
        }
        #go2-examples li { color: #8aa0ab; font-size: 0.88rem; margin-bottom: 3px; }
        </style>
        <div id="go2-header">
            <h1>🤖 Go2 Robot Assistant</h1>
            <span class="tag">MCP · Live</span>
        </div>
        <div id="go2-sub">
            Ask about topics, sensors, or system state — or issue a direct control command.
        </div>
        """
    )

    with gr.Row():

        with gr.Column(scale=4):

            chatbot = gr.Chatbot(
                label="ROS2 MCP Assistant",
                height=600,
                elem_id="go2-chat",
            )

            with gr.Row():

                user_input = gr.Textbox(
                    placeholder=(
                        "Ask something about the robot..."
                    ),
                    label="Command",
                    scale=5,
                    lines=2,
                    elem_id="go2-input",
                )

                send_btn = gr.Button(
                    "Send",
                    variant="primary",
                    scale=1,
                    elem_id="go2-send",
                )

            clear_btn = gr.Button(
                "Clear Conversation"
            )

        with gr.Column(scale=1):

            status = gr.Textbox(
                label="Agent Status",
                value="Ready",
                interactive=False,
                lines=3,
                elem_id="go2-status",
            )

            gr.HTML(
                """
                <div id="go2-examples">
                <h3>Example commands</h3>
                <ul>
                    <li>What is the robot's battery?</li>
                    <li>What ROS2 topics are available?</li>
                    <li>What is the current robot position?</li>
                    <li>Check the camera status.</li>
                    <li>What sensors are connected?</li>
                    <li>Move the robot forward.</li>
                    <li>Stop the robot.</li>
                    <li>Rotate left.</li>
                </ul>
                </div>
                """
            )

    # ---------------------------------------
    # Send button
    # ---------------------------------------

    send_event = send_btn.click(
        fn=chatbot_response,
        inputs=[
            user_input,
            chatbot,
        ],
        outputs=[
            chatbot,
            user_input,
            status,
        ],
    )

    # ---------------------------------------
    # Enter key
    # ---------------------------------------

    user_input.submit(
        fn=chatbot_response,
        inputs=[
            user_input,
            chatbot,
        ],
        outputs=[
            chatbot,
            user_input,
            status,
        ],
    )

    # ---------------------------------------
    # Clear
    # ---------------------------------------

    clear_btn.click(
        fn=clear_chat,
        inputs=None,
        outputs=[
            chatbot,
            user_input,
            status,
        ],
    )

    return chatbot
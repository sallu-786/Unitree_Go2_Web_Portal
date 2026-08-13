from litellm import completion
from config import (
    LLM_MODE, MODELS, DEFAULT_MODEL, AZURE_API_BASE, AZURE_API_KEY,
    AZURE_API_VERSION, OLLAMA_API_BASE, OLLAMA_API_KEY)

class GenerateVLA:
    def __init__(self):

        model_key = DEFAULT_MODEL[LLM_MODE]
        self.model = MODELS[LLM_MODE][model_key]

        if LLM_MODE == "azure":
            self.api_base = AZURE_API_BASE
            self.api_key = AZURE_API_KEY
            self.api_version = AZURE_API_VERSION
        else:
            self.api_base = OLLAMA_API_BASE
            self.api_key = OLLAMA_API_KEY
            self.api_version = None

        self.system_message = (
            "You are a navigation module for a quadruped robot. "
            "Look at the image and decide the next move. "
            "Respond with ONLY one word, no punctuation: "
            "forward, left, right, backward, or stop."
        )
        self.user_message = "What should the robot do next?"

    def vla_response(self, image_path):

        messages = [
            {
                "role": "system",
                "content": self.system_message
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": self.user_message},
                    {"type": "image_url", "image_url": {"url": image_path}}
                ]
            }
        ]

        response = completion(
            model=self.model,
            messages=messages,
            max_tokens=5,
            temperature=0.1,
            stream=False,
            api_base=self.api_base,
            api_key=self.api_key,
            api_version=self.api_version
        )
        action = response.choices[0].message.content.strip().lower()
        return action if action in ("forward", "left", "right", "backward", "stop") else "stop"

    def action_to_cmd(self, action):
        return {
            "forward":  (0.3, 0.0, 0.0),
            "backward": (-0.3, 0.0, 0.0),
            "left":     (0.0, 0.0, 0.5),
            "right":    (0.0, 0.0, -0.5),
            "stop":     (0.0, 0.0, 0.0),
        }.get(action, (0.0, 0.0, 0.0))
from litellm import completion
from config import (
    LLM_MODE,MODELS,DEFAULT_MODEL,AZURE_API_BASE,AZURE_API_KEY,AZURE_API_VERSION,OLLAMA_API_BASE,OLLAMA_API_KEY,SYSTEM_PROMPT,LLM_PROMPT)
from rclpy.node import Node
class GenerateResponse(Node):
    def __init__(self):
        super().__init__('llm_subscriber')

        model_key = DEFAULT_MODEL[LLM_MODE]
        self.model = MODELS[LLM_MODE][model_key]
        self.get_logger().info("LLM based Image explainer (GenerateResponse) initialized")
        

        if LLM_MODE == "azure":
            self.api_base = AZURE_API_BASE
            self.api_key = AZURE_API_KEY
            self.api_version = AZURE_API_VERSION
        else:
            self.api_base = OLLAMA_API_BASE
            self.api_key = OLLAMA_API_KEY
            self.api_version = None  # not needed

        self.system_message = SYSTEM_PROMPT
        self.user_message = LLM_PROMPT

    def llm_response(self, image_path=None):

        if image_path is None:
            messages = [
                {
                    "role": "system",
                    "content": self.system_message
                },
                {
                    "role": "user",
                    "content": "There is no camera image attached. Tell the user briefly that no camera is connected."
                }
            ]
        else:
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

        # messages = [
        #     {
        #         "role": "system",
        #         "content": f"{self.system_message}. If you see warning or accident highlight it.if there is no image tell user the is no image attached. please check camera stream"
        #     },
        #     {
        #         "role": "user",
        #         "content": [
        #             {"type": "text", "text": self.user_message},
        #             {"type": "image_url", "image_url": {"url": image_path}}
        #         ]
        #     }
        # ]

        response = completion(
            model=self.model,
            messages=messages,
            max_tokens=150,
            temperature=0.7,
            stream=False,
            api_base=self.api_base,
            api_key=self.api_key,
            api_version=self.api_version
        )
        return response.choices[0].message.content.strip()
from services.ai_service import AIService
import requests
from PIL import Image
import io
import os
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
import os
import time
import json

class OpenAIService(AIService):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def run_llm(self, messages, stream = True):
        messages_for_log = json.dumps(messages)
        self.logger.error(f"==== generating chat via openai: {messages_for_log}")

        model = os.getenv("OPEN_AI_MODEL")
        if not model:
            model = "gpt-4"

        response = client.chat.completions.create(
            messages=messages,
            model="gpt-4",
            stream=stream
        )

        return response

    def run_image_gen(self, sentence):
        self.logger.info("🖌️ generating openai image async for ", sentence)
        start = time.time()

        image = client.images.generate(api_type = 'openai',
        api_version = '2020-11-07',
        api_base = "https://api.openai.com/v1",
        api_key = os.getenv("OPEN_AI_KEY"),
        prompt=f'{sentence} in the style of {self.image_style}',
        n=1,
        size=f"1024x1024")
        image_url = image["data"][0]["url"]
        self.logger.info("🖌️ generated image from url", image["data"][0]["url"])
        response = requests.get(image_url)
        self.logger.info("🖌️ got image from url", response)
        dalle_stream = io.BytesIO(response.content)
        dalle_im = Image.open(dalle_stream)
        self.logger.info("🖌️ total time", time.time() - start)

        return (image_url, dalle_im)

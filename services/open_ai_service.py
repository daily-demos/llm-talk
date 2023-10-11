from services.ai_service import AIService
import requests
from PIL import Image
import io
import openai
import os

class OpenAIService(AIService):
    def __init__(self):
        # we handle all the api config directly in the calls below
        pass

    def run_llm(self, messages, stream = True):
        model = os.getenv("OPEN_AI_MODEL")
        if not model:
            model = "gpt-4"
        response = openai.ChatCompletion.create(
            api_type = 'openai',
            api_version = '2020-11-07',
            api_base = "https://api.openai.com/v1",
            api_key = os.getenv("OPEN_AI_KEY"),
            model=model,
            stream=stream,
            messages=messages
        )

        return response

    def run_image_gen(self, sentence):
        print("🖌️ generating openai image async for ", sentence)

        image = openai.Image.create(
            api_type = 'openai',
            api_version = '2020-11-07',
            api_base = "https://api.openai.com/v1",
            api_key = os.getenv("OPEN_AI_KEY"),
            prompt=f'{sentence} in the style of {self.image_style}',
            n=1,
            size=f"512x512",
        )
        image_url = image["data"][0]["url"]
        print("🖌️ generated image from url", image["data"][0]["url"])
        response = requests.get(image_url)
        print("🖌️ got image from url", response)
        dalle_stream = io.BytesIO(response.content)
        dalle_im = Image.open(dalle_stream)
        return (image_url, dalle_im)

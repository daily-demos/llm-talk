import json
import io
import openai
import os
import requests

from services.ai_service import AIService
from PIL import Image

# See .env.example for Azure configuration needed
from azure.cognitiveservices.speech import SpeechSynthesizer, SpeechConfig, ResultReason, CancellationReason

class AzureAIService(AIService):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.speech_key = os.getenv("AZURE_SPEECH_SERVICE_KEY")
        self.speech_region = os.getenv("AZURE_SPEECH_SERVICE_REGION")

        self.speech_config = SpeechConfig(subscription=self.speech_key, region=self.speech_region)
        # self.speech_config.speech_synthesis_voice_name='en-US-JennyMultilingualV2Neural'

        self.speech_synthesizer = SpeechSynthesizer(speech_config=self.speech_config, audio_config=None)

    def run_tts(self, sentence):
        self.logger.info("⌨️ running azure tts async")
        ssml = "<speak version='1.0' xml:lang='en-US' xmlns='http://www.w3.org/2001/10/synthesis' " \
           "xmlns:mstts='http://www.w3.org/2001/mstts'>" \
           "<voice name='en-US-SaraNeural'>" \
           "<mstts:silence type='Sentenceboundary' value='20ms' />" \
           "<mstts:express-as style='lyrical' styledegree='2' role='SeniorFemale'>" \
           "<prosody rate='1.05'>" \
           f"{sentence}" \
           "</prosody></mstts:express-as></voice></speak> "
        result = self.speech_synthesizer.speak_ssml(ssml)
        self.logger.info("⌨️ got azure tts result")
        if result.reason == ResultReason.SynthesizingAudioCompleted:
            self.logger.info("⌨️ returning result")
            # azure always sends a 44-byte header. Strip it off.
            yield result.audio_data[44:]
        elif result.reason == ResultReason.Canceled:
            cancellation_details = result.cancellation_details
            self.logger.info("Speech synthesis canceled: {}".format(cancellation_details.reason))
            if cancellation_details.reason == CancellationReason.Error:
                self.logger.info("Error details: {}".format(cancellation_details.error_details))

    # generate a chat using Azure OpenAI based on the participant's most recent speech
    def run_llm(self, messages, stream = True):
        messages_for_log = json.dumps(messages)
        self.logger.error(f"==== generating chat via azure openai: {messages_for_log}")

        response = openai.ChatCompletion.create(
            api_type = 'azure',
            api_version = '2023-06-01-preview',
            api_key = os.getenv("AZURE_CHATGPT_KEY"),
            api_base = os.getenv("AZURE_CHATGPT_ENDPOINT"),
            deployment_id=os.getenv("AZURE_CHATGPT_DEPLOYMENT_ID"),
            stream=stream,
            messages=messages
        )
        return response

    def run_image_gen(self, sentence):
        self.logger.info("generating azure image", sentence)

        image = openai.Image.create(
            api_type = 'azure',
            api_version = '2023-06-01-preview',
            api_key = os.getenv('AZURE_DALLE_KEY'),
            api_base = os.getenv('AZURE_DALLE_ENDPOINT'),
            deployment_id = os.getenv("AZURE_DALLE_DEPLOYMENT_ID"),
            prompt=f'{sentence} in the style of {self.image_style}',
            n=1,
            size=f"1024x1024",
        )

        url = image["data"][0]["url"]
        response = requests.get(url)

        dalle_stream = io.BytesIO(response.content)
        dalle_im = Image.open(dalle_stream)

        return (url, dalle_im)

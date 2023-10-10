import argparse
import os
import random
import re
import time
from threading import Thread

from daily import EventHandler, CallClient, Daily
from datetime import datetime
from dotenv import load_dotenv

import config

from orchestrator import Orchestrator
from scenes.story_intro_scene import StoryIntroScene
from scenes.start_listening_scene import StartListeningScene

load_dotenv()

class DailyLLM(EventHandler):
    def __init__(
            self,
            room_url=os.getenv("DAILY_URL"),
            token=os.getenv('DAILY_TOKEN'),
            bot_name="Storybot",
            image_style="watercolor illustrated children's book", # keep the generated images to a certain theme, like "golden age of illustration," "talented kid's crayon drawing", etc.
        ):

        # room + bot details
        self.room_url = room_url
        room_name = get_room_name(room_url)
        if token:
            self.token = token
        else:
            self.token = get_meeting_token(room_name, os.getenv("DAILY_API_KEY"))
        self.bot_name = bot_name
        self.image_style = image_style

        duration = os.getenv("BOT_MAX_DURATION")
        if not duration:
            duration = 300
        else:
            duration = int(duration)
        self.expiration = time.time() + duration
        self.story_started = False
        self.current_prompt = ''

        self.finished_talking_at = None


        print(f"{room_url} Joining", self.room_url, "as", self.bot_name, "leaving at", self.expiration, "current time is", time.time())

        self.print_debug(f"expiration: {datetime.utcfromtimestamp(self.expiration).strftime('%Y-%m-%d %H:%M:%S')}")
        self.print_debug(f"now: {datetime.utcfromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')}")

        self.my_participant_id = None

        self.print_debug("configuring services")
        self.configure_ai_services()
        self.print_debug("configuring daily")
        self.configure_daily()

        self.stop_threads = False
        self.image = None

        self.print_debug("starting camera thread")
        self.camera_thread = Thread(target=self.run_camera)
        self.camera_thread.start()

        self.print_debug("starting orchestrator")
        self.orchestrator = Orchestrator(self, self.mic, self.tts, self.image_gen, self.llm, self.story_id)
        self.orchestrator.enqueue(StoryIntroScene)
        self.orchestrator.enqueue(StartListeningScene)

        self.participant_left = False
        self.transcription = ""
        self.last_fragment_at = None

        try:
            participant_count = len(self.client.participants())
            self.print_debug(f"{participant_count} participants in room")
            while time.time() < self.expiration and not self.participant_left:
                # all handling of incoming transcriptions happens in on_transcription_message
                if self.last_fragment_at is not None and (time.time() > self.last_fragment_at + 5):
                    # They probably stopped talking, but Deepgram didn't give us a complete sentence
                    print(f"Sending transcript due to timeout: {self.transcription}")
                    self.send_transcription()
                time.sleep(1)
        except Exception as e:
            self.print_debug(f"Exception {e}")
        finally:
            self.client.leave()

        self.stop_threads = True
        self.print_debug("Shutting down")
        self.camera_thread.join()
        self.print_debug("camera thread stopped")

    def print_debug(self, s):
        print(f"{self.room_url} {s}", flush=True)

    def configure_ai_services(self):
        self.story_id = hex(random.getrandbits(128))[2:]

        self.tts = config.services[os.getenv("TTS_SERVICE")]()
        self.image_gen = config.services[os.getenv("IMAGE_GEN_SERVICE")]()
        self.llm = config.services[os.getenv("LLM_SERVICE")]()

    def configure_daily(self):
        Daily.init()
        self.client = CallClient(event_handler = self)

        self.mic = Daily.create_microphone_device("mic", sample_rate = 16000, channels = 1)
        self.speaker = Daily.create_speaker_device("speaker", sample_rate = 16000, channels = 1)
        self.camera = Daily.create_camera_device("camera", width = 512, height = 512, color_format="RGB")

        self.image_gen.set_image_style(self.image_style)

        Daily.select_speaker_device("speaker")

        self.client.set_user_name(self.bot_name)
        self.client.join(self.room_url, self.token, completion=self.call_joined)

        self.client.update_inputs({
            "camera": {
                "isEnabled": True,
                "settings": {
                    "deviceId": "camera"
                }
            },
            "microphone": {
                "isEnabled": True,
                "settings": {
                    "deviceId": "mic"
                }
            }
        })

        self.my_participant_id = self.client.participants()['local']['id']

    def call_joined(self, join_data, client_error):
        self.print_debug(f"call_joined: {join_data}, {client_error}")
        self.client.start_transcription()

    def on_participant_updated(self, participant):
        pass

    def on_call_state_updated(self, call_state):
        pass

    def on_inputs_updated(self, inputs):
        pass

    def on_participant_counts_updated(self, participant_counts):
        pass

    def on_active_speaker_changed(self, active_speaker):
        pass

    def on_network_stats_updated(self, network_stats):
        pass

    def on_participant_joined(self, participant):
        self.print_debug(f"on_participant_joined: {participant}")
        self.client.send_app_message({ "event": "story-id", "storyID": self.story_id})
        self.wave()
        time.sleep(2)

        # don't run intro question for newcomers
        if not self.story_started:
            #self.orchestrator.request_intro()
            self.orchestrator.action()
            self.story_started = True

    def on_participant_left(self, participant, reason):
        if len(self.client.participants()) < 2:
            self.print_debug("participant left")
            self.participant_left = True

    def send_transcription(self):
        self.orchestrator.handle_user_speech(self.transcription)
        self.transcription = ""
        self.last_fragment_at = None

    def on_transcription_message(self, message):
        # TODO: This should maybe match on my own participant id instead but I'm in a hurry
        if message['session_id'] != self.my_participant_id:
            if self.orchestrator.started_listening_at:
                # TODO: Check actual transcription timestamp against started_listening_at
                self.transcription += f" {message['text']}"
                # Deepgram says we should look for ending punctuation
                if re.search(r'[\.\!\?]$', self.transcription):
                    print(f"✏️ Sending reply: {self.transcription}")
                    self.send_transcription()
                else:
                    print(f"✏️ Got a transcription fragment: \"{self.transcription}\"")
                    self.last_fragment_at = time.time()


    def set_image(self, image):
        self.image = image

    def run_camera(self):
        try:
            while not self.stop_threads:
                if self.image:
                    self.camera.write_frame(self.image.tobytes())
                time.sleep(1.0 / 15.0) # 15 fps
        except Exception as e:
            self.print_debug(f"Exception {e} in camera thread.")

    def wave(self):
        self.client.send_app_message({
            "event": "sync-emoji-reaction",
            "reaction": {
                "emoji": "👋",
                "room": "main-room",
                "sessionId": "bot",
                "id": time.time(),
            }
        })

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Daily LLM bot")
    parser.add_argument("-u", "--url", type=str, help="URL of the Daily room")
    parser.add_argument("-t", "--token", type=str, help="Token for Daily API")
    parser.add_argument("-b", "--bot-name", type=str, help="Name of the bot")

    args = parser.parse_args()

    url = args.url or os.getenv("DAILY_URL")
    bot_name = args.bot_name or "Storybot"
    token = args.token or None

    app = DailyLLM(url, token, bot_name)

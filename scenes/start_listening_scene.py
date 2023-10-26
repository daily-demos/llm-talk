from scenes.scene import Scene
from threading import Thread
import os
import wave
from PIL import Image

class StartListeningScene(Scene):
	def __init__(self, **kwargs):
		script_dir = os.path.dirname(__file__)
		rel_path = "../ai.wav"
		abs_file_path = os.path.join(script_dir, rel_path)
		with wave.open(abs_file_path) as audio_file:
			# Get audio data as a bytestream
			self.ai_complete_sound = audio_file.readframes(-1)

		super().__init__(**kwargs)
		self.logger.info("📣 StartListeningScene init")

	def prepare(self):
		self.logger.info("📣 StartListeningScene prepare")
		# don't need threads here because image
		# is effectively instant
		self.scene_data['image'] = self.grandma_listening
		self.scene_data['audio'] = [self.ai_complete_sound]
		self.logger.info("📣 StartListeningScene prepare complete")


	def perform(self):
		self.logger.info("📣 StartListeningScene perform")
		self.orchestrator.start_listening()
		super().perform()

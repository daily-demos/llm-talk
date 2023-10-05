from scenes.scene import Scene
from threading import Thread
import os
import wave

class StopListeningScene(Scene):
	def __init__(self, **kwargs):
		print("🤫 StopListeningScene init")
		script_dir = os.path.dirname(__file__)
		rel_path = "../human.wav"
		abs_file_path = os.path.join(script_dir, rel_path)
		with wave.open(abs_file_path) as audio_file:
			# Get audio data as a bytestream
			self.human_complete_sound = audio_file.readframes(-1)
		super().__init__(**kwargs)
		
	def prepare(self):
		print("🤫 StopListeningScene prepare")
		# don't need threads here because image
		# is effectively instant
		self.scene_data['image'] = self.grandma_writing
		self.scene_data['audio'] = self.human_complete_sound
		print("🤫 StopListeningScene prepare complete")
		
	
	def perform(self):
		print("🤫 StopListeningScene perform")
		self.orchestrator.stop_listening()
		super().perform()
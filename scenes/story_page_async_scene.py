from scenes.scene import Scene
from threading import Thread

# This is the async version that will try to display the image
# as soon as it's ready.
class StoryPageAsyncScene(Scene):
	def __init__(self, **kwargs):
		print("StoryPageScene init")
		self.sentence = kwargs.get('sentence', None)
		self.image = kwargs.get('image', False)
		super().__init__(**kwargs)

	def fetch_audio(self):
		self.scene_data['audio'] = self.orchestrator.request_tts(self.sentence)
		print(f"🌆 fetch audio complete for {self.sentence}")

	def fetch_image(self):
		if self.image:
			self.scene_data['image'] = self.orchestrator.request_image(self.sentence)
			print(f"🌆 fetch image complete for {self.sentence}")
		else:
			print(f"🌆 Skipping image for {self.sentence}")


	def prepare(self):
		print(f"🌆 StoryPageScene prepare sentence: {self.sentence}")
		# Get intro prompt, then
		self.image_thread = Thread(target=self.fetch_image)
		self.image_thread.start()
		self.audio_thread = Thread(target=self.fetch_audio)
		self.audio_thread.start()

		#self.image_getter.join()
		if self.audio_thread:
			self.audio_thread.join()
		print(f"🌆 StoryPageScene prepare complete for: {self.sentence}")


	def perform(self):
		print(f"🌆 StoryPageScene perform sentence: {self.sentence}")
		super().perform()

from scenes.scene import Scene
from threading import Thread

# This is the async version that will try to display the image
# as soon as it's ready.
class StoryPageAsyncScene(Scene):
	def __init__(self, **kwargs):
		print("StoryPageScene init")
		self.sentence = kwargs.get('sentence', None)
		self.image = kwargs.get('image', False)
		self.story_sentences = kwargs.get('story_sentences', None)
		super().__init__(**kwargs)

	def fetch_audio(self):
		try:
			self.scene_data['audio'] = self.orchestrator.request_tts(self.sentence)
			print(f"🌆 fetch audio complete for {self.sentence}")
		except Exception as e:
			print(f"Exception in fetch_audio {e}")

	def fetch_image(self):
		try:
			if self.image:
				desc = self.orchestrator.request_image_description(self.story_sentences)
				
				(url, image) = self.orchestrator.request_image(desc)
				(self.scene_data['url'], self.scene_data['image']) = (url, image)
				print(f"🌆 fetch image complete for {self.sentence}")
			else:
				print(f"🌆 Skipping image for {self.sentence}")
		except Exception as e:
			print(f"Exception in fetch_image {e}")


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
		self.orchestrator.index_scene(self)

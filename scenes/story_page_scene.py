from scenes.scene import Scene
from threading import Thread

# This is the synchronous version
class StoryPageScene(Scene):
	def __init__(self, **kwargs):
		self.sentence = kwargs.get('sentence', None)
		super().__init__(**kwargs)
		self.logger.info("StoryPageScene init")

	def fetch_audio(self):
		try:
			self.scene_data['audio'] = self.orchestrator.request_tts(self.sentence)
			self.logger.info(f"🌆 fetch audio complete for {self.sentence}")
		except Exception as e:
			self.logger.error(f"Exception in fetch_audio {e}")

	def fetch_image(self):
		try:
			(url, image) = self.orchestrator.request_image(self.sentence)
			(self.scene_data['url'], self.scene_data['image']) = (url, image)
			self.logger.info(f"🌆 fetch image complete for {self.sentence}")
		except Exception as e:
			self.logger.error(f"Exception in fetch_image {e}")

	def prepare(self):
		self.logger.info(f"🌆 StoryPageScene prepare sentence: {self.sentence}")
		# Get intro prompt, then
		self.image_getter = Thread(target=self.fetch_image)
		self.image_getter.start()
		self.audio_getter = Thread(target=self.fetch_audio)
		self.audio_getter.start()

		self.image_getter.join()
		self.audio_getter.join()
		self.logger.info(f"🌆 StoryPageScene prepare complete for: {self.sentence}")


	def perform(self):
		self.logger.info(f"🌆 StoryPageScene perform sentence: {self.sentence}")
		super().perform()
		self.orchestrator.index_scene(self)


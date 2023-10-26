from scenes.scene import Scene
from threading import Thread

class StoryGrandmaScene(Scene):
	def __init__(self, **kwargs):
		self.sentence = kwargs.get('sentence', None)
		super().__init__(**kwargs)
		print("StoryGrandmaScene init")

	def prepare(self):
		print(f"👩‍💼 StoryGrandmaScene prepare sentence: {self.sentence}")
		# don't need threads here because image
		# is effectively instant
		self.scene_data['image'] = (self.grandma_writing)
		self.scene_data['audio'] = self.orchestrator.request_tts(self.sentence)
		print(f"👩‍💼 StoryGrandmaScene prepare complete for: {self.sentence}")


	def perform(self):
		print(f"👩‍💼 StoryGrandmaScene perform sentence: {self.sentence}")
		super().perform()

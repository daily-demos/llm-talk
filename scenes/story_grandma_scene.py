from scenes.scene import Scene
from threading import Thread

class StoryGrandmaScene(Scene):
	def __init__(self, **kwargs):
		print("StoryPageScene init")
		self.sentence = kwargs.get('sentence', None)
		super().__init__(**kwargs)
		
	def prepare(self):
		print(f"👩‍💼 StoryStartScene prepare sentence: {self.sentence}")
		# don't need threads here because image
		# is effectively instant
		self.scene_data['image'] = (self.grandma_writing)
		self.scene_data['audio'] = self.orchestrator.request_tts(self.sentence)
		print(f"👩‍💼 StoryStartScene prepare complete for: {self.sentence}")
		
	
	def perform(self):
		print(f"👩‍💼 StoryStartScene perform sentence: {self.sentence}")
		super().perform()
from scenes.scene import Scene

class StoryIntroScene(Scene):
	def __init__(self, **kwargs):
		print("StoryIntroScene init")
		super().__init__(**kwargs)
		pass
		
	def prepare(self):
		print("StoryIntroScene prepare")
		# Get intro prompt, then
		self.scene_data['image'] = self.grandma_listening
		self.scene_data['audio'] = self.orchestrator.request_intro()
		
	
	def perform(self):
		print("StoryIntroScene perform")
		super().perform()
		pass
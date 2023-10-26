from scenes.scene import Scene

class StoryIntroScene(Scene):
	def __init__(self, **kwargs):
		super().__init__(**kwargs)
		self.logger.info("StoryIntroScene init")

	def prepare(self):
		self.logger.info("StoryIntroScene prepare")
		# Get intro prompt, then
		self.scene_data['image'] = self.grandma_listening
		self.scene_data['audio'] = self.orchestrator.request_intro()


	def perform(self):
		self.logger.info("StoryIntroScene perform")
		super().perform()
		pass

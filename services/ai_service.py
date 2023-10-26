from abc import abstractmethod
import logging

class AIService:
    def __init__(self, **kwargs):
        self.image_style = None
        self.logger = kwargs.get('logger', logging.getLogger('ai-service'))

    def close(self):
        # most services don't need to do anything here
        pass

    def set_image_style(self, image_style):
        self.image_style = image_style

    # Speak the sentence. Returns None
    @abstractmethod
    def run_tts(self, sentence):
        pass

    # Generate an image from the sentence. Returns an image
    @abstractmethod
    def run_image_gen(self, sentence):
        pass

    # Generate a set of responses to a prompt. Yields a list of responses.
    @abstractmethod
    def run_llm(self, context, human_histories, llm_histories, prompt):
        pass

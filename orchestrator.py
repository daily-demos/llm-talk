import json
import io
import random
import re
import time
from datetime import datetime
from queue import Queue
from queue import Empty

from search import SearchIndexer
from services.mock_ai_service import MockAIService
from scenes.story_page_scene import StoryPageScene
from scenes.story_page_async_scene import StoryPageAsyncScene

from scenes.story_grandma_scene import StoryGrandmaScene
from scenes.stop_listening_scene import StopListeningScene
from scenes.start_listening_scene import StartListeningScene

from threading import Thread

class Orchestrator():
    def __init__(self, image_setter, microphone, ai_tts_service, ai_image_gen_service, ai_llm_service, story_id):
        self.image_setter = image_setter
        self.microphone = microphone

        self.ai_tts_service = ai_tts_service
        self.ai_image_gen_service = ai_image_gen_service
        self.ai_llm_service = ai_llm_service

        self.search_indexer = SearchIndexer(story_id)

        self.tts_getter = None
        self.image_getter = None

        self.messages = [{"role": "system", "content": "You are a storyteller who loves to make up fantastic, fun, and educational stories for children between the ages of 5 and 10 years old. Your stories are full of friendly, magical creatures. Your stories are never scary. Each sentence of your story will become a page in a storybook. Stop after 4-6 sentences and give the child a choice to make that will influence the next part of the story. Once the child responds, start by saying something nice about the choice they made, then include [start] in your response. Include [break] after each sentence of the story. Include [prompt] between the story and the prompt."}]
        self.intro_messages = [{"role": "system", "content": "You are a storyteller who loves to make up fantastic, fun, and educational stories for children between the ages of 5 and 10 years old. Your stories are full of friendly, magical creatures. Your stories are never scary. Begin by asking what a child wants you to tell a story about."}]

        self.llm_response_thread = None

        self.scene_queue = Queue()
        self.stop_threads = False
        self.started_listening_at = None
        self.image_this_time = True



    def handle_user_speech(self, user_speech):
        print(f"👅 Handling user speech: {user_speech}")
        if not self.llm_response_thread or not self.llm_response_thread.is_alive():
            self.enqueue(StopListeningScene)
            self.llm_response_thread = Thread(target=self.request_llm_response, args=(user_speech,))
            self.llm_response_thread.start()
        else:
            print("discarding overlapping speech, TODO barge-in")

    def start_listening(self):
        self.started_listening_at = datetime.now()

    def stop_listening(self):
        self.started_listening_at = None

    def listening_since(self):
        return self.started_listening_at

    def request_llm_response(self, user_speech):
        try:
            self.messages.append({"role": "user", "content": user_speech})
            response = self.ai_llm_service.run_llm(self.messages)
            self.handle_llm_response(response)
        except Exception as e:
            print(f"Exception in request_llm_response: {e}")

    def request_intro(self):
        response = self.ai_llm_service.run_llm(self.intro_messages)
        return self.handle_intro(response)

    def handle_intro(self, llm_response):
        # Do this all as one piece, at least for now
        out = ''
        for chunk in llm_response:
            if len(chunk["choices"]) == 0:
                continue
            if "content" in chunk["choices"][0]["delta"]:
                if chunk["choices"][0]["delta"]["content"] != {}: #streaming a content chunk
                    next_chunk = chunk["choices"][0]["delta"]["content"]
                    out += next_chunk
        return self.ai_tts_service.run_tts(out)

    def handle_llm_response(self, llm_response):
        out = ''
        full_response = ''
        prompt_started = False
        for chunk in llm_response:
            if len(chunk["choices"]) == 0:
                continue
            if "content" in chunk["choices"][0]["delta"]:
                if chunk["choices"][0]["delta"]["content"] != {}: #streaming a content chunk
                    next_chunk = chunk["choices"][0]["delta"]["content"]
                    out += next_chunk
                    full_response += next_chunk
                    #print(f"🎬 Out: {out}")

                    #if re.match(r'^.*[.!?]$', out): # it looks like a sentence
                    if prompt_started == False:
                        if re.findall(r'.*\[[sS]tart\].*', out):
                            # Then we have the intro. Send it to speech ASAP
                            out = out.replace("[Start]", "")
                            out = out.replace("[start]", "")

                            out = out.replace("\n", " ")
                            if len(out) > 2:
                                self.enqueue(StoryGrandmaScene, sentence=out)
                            out = ''

                        elif re.findall(r'.*\[[bB]reak\].*', out):
                            # Then it's a page of the story. Get an image too
                            out = out.replace("[Break]", "")
                            out = out.replace("[break]", "")
                            out = out.replace("\n", " ")
                            if len(out) > 2:
                                self.enqueue(StoryPageAsyncScene, sentence=out, image=self.image_this_time)

                                self.image_this_time = not self.image_this_time

                            out = ''
                        elif re.findall(r'.*\[[pP]rompt\].*', out):
                            # Then it's question time. Flush any
                            # text here as a story page, then set
                            # the var to get to prompt mode
                            #cb: trying scene now
                            # self.handle_chunk(out)
                            out = out.replace("[Prompt]", "")
                            out = out.replace("[prompt]", "")

                            out = out.replace("\n", " ")
                            if len(out) > 2:
                                self.enqueue(StoryPageAsyncScene, sentence=out, image=self.image_this_time)
                                self.image_this_time =  not self.image_this_time

                            out = ''
                    else:
                        # Just get the rest of the output as the prompt
                        pass


                        out = ''
        # get the last one too; it should be the prompt
        print(f"🎬 FINAL Out: {out}")
        self.enqueue(StoryGrandmaScene, sentence=out)
        self.enqueue(StartListeningScene)
        print(f"🎬 FULL MESSAGE: {full_response}")
        self.messages.append({"role": "assistant", "content": full_response})
        self.image_this_time = False

    def handle_chunk(self, chunk):
        #self.llm_history.append(chunk)

        self.tts_getter = Thread(target=self.request_tts, args=(chunk,))
        self.tts_getter.start()
        self.image_getter = Thread(target=self.request_image, args=(chunk,))
        self.image_getter.start()

        self.tts_getter.join()
        self.image_getter.join()

    def request_tts(self, text):
        try:
            audio = self.ai_tts_service.run_tts(text)
            return audio
        except Exception as e:
            print(f"Exception in request_tts: {e}")

    def request_image(self, text):
        try:
            (url, image) = self.ai_image_gen_service.run_image_gen(text)
            return (url, image)
        except Exception as e:
            print(f"Exception in request_image: {e}")

    def handle_audio(self, audio):
        print("🏙️ orchestrator handle audio")
        stream = io.BytesIO(audio)

        # Skip RIFF header
        stream.read(44)
        self.microphone.write_frames(stream.read())

    def display_image(self, image):
        if self.image_setter:
            self.image_setter.set_image(image)

    def enqueue(self, scene_type, **kwargs):
        # Take the newly created scene object, call its prepare function, and queue it to perform
        kwargs['orchestrator'] = self
        self.scene_queue.put(scene_type(**kwargs))
        pass

    def action(self):
        # start playing scenes. This allows us to prepare scenes
        # before we actually start playback
        self.playback_thread = Thread(target=self.playback)
        self.playback_thread.start()

    def index_scene_async(self, scene):
        self.search_indexer.index_text(scene.sentence)
        if 'url' in scene.scene_data:
            self.search_indexer.index_image(scene.scene_data['url'])

    def index_scene(self, scene):
        if 'sentence' in scene.__dict__:
            thread = Thread(target=self.index_scene_async, args=(scene,))
            thread.start()
            # we let this thread run unattended

    def playback(self):
        while True:
            try:
                if self.stop_threads:
                    print("🎬 Shutting down playback thread")
                    break
                scene = self.scene_queue.get(block=False)
                if 'sentence' in scene.__dict__:
                    print(f"🎬 Performing scene: {type(scene).__name__}, {scene.sentence}")
                else:
                    print(f"🎬 Performing sentenceless scene: {type(scene).__name__}")
                scene.perform()
                time.sleep(0)
            except Empty:
                time.sleep(0.1)
                continue


if __name__ == "__main__":
    mock_ai_service = MockAIService()
    class MockImageSetter():
        def set_image(self, image):
            print("setting image", image)

    class MockMicrophone():
        def write_frames(self, frames):
            print("writing frames")

    uim = Orchestrator("context", MockImageSetter(), MockMicrophone(), mock_ai_service, mock_ai_service, mock_ai_service, 0)
    uim.handle_user_speech("hello world")


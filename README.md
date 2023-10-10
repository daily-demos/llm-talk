# Daily LLM

## Overview

This project lets you talk to an AI participant in a Daily call. The AI participant will talk to you just like anybody else on the call, and you can configure their behavior based on your use case.

## Key ingredients

- [`daily-python`](https://beta-python.daily.co/index.html), Daily's own Python library which lets you pipe audio and video in and out of a Daily call
- [`Daily Transcription powered by Deepgram`](https://docs.daily.co/reference/rn-daily-js/instance-methods/start-transcription#main), which generates text from your in-call speech
- [`Azure Speech Service`](https://azure.microsoft.com/en-us/products/ai-services/ai-speech), a text-to-speech service with dozens of configurable voices
- [`Azure OpenAI`](https://azure.microsoft.com/en-us/products/ai-services/openai-service), an LLM running on OpenAI to return intelligent, context-aware chat completions from any text you send its way
- [`Algolia InstantSearch`](https://www.algolia.com/doc/api-reference/widgets/instantsearch/js/), an easy way to make the generated stories full-text searchable

# Getting started

## Enable Daily's transcription service

This demo uses Daily's transcription (powered by deepgram.com) to convert your in-call audio to text, so it can then be passed to an LLM.

Once you're signed up for Daily and Deepgram, you'll just need to set the [`enable transcription`](https://docs.daily.co/reference/rest-api/your-domain/config#enable_transcription) property on your domain.

## Choose your cloud providers and update your `ENV` variables

Copy `.env.example` to `.env` and include the appropriate keys for your chosen LLM, TTS, and image generation services. You can mix and match; the supported values for each are:

- `TTS_SERVICE`: `google` or `azure`
- `LLM_SERVICE`: `openai` or `azure` (running Azure OpenAI)
- `IMAGE_GEN_SERVICE`: `openai` or `azure` (running Azure OpenAI)

Depending on which service you're using, you'll need to set other variables in your .env file. The env.example file should point you in the right direction.

If you're using Azure, you can find the values from your [Azure Dashboard](https://portal.azure.com/) in the **Keys and Endpoints** tab for your chosen AI service.

> ❗️Note that the Azure OpenAI keys are _not_ the same ones you'd get from [platform.openai.com](https://platform.openai.com). The keyword arguments for the completion endpoints may also be slightly different than you're used to. For more detail, check out [How to switch between OpenAI and Azure OpenAI endpoints with Python](https://learn.microsoft.com/en-us/azure/ai-services/openai/how-to/switching-endpoints).

### Google Cloud configuration

If you want to use Google Cloud, it's a little different; instead of using `ENV` variables, you'll need to [install the gcloud CLI](https://cloud.google.com/sdk/docs/install).

Currently, we're _not_ using Google Cloud's text-generation capabilities, so you'll need to include a `OPEN_AI_KEY` environment variable.

### Algolia configuration

If you'd like your stories to be saved and searchable for later, include these `ENV` variables:

- `ALGOLIA_APP_ID`
- `ALGOLIA_API_KEY`

Also edit `read.example.html` with your correct `ALGOLIA_APP_ID` and `ALGOLIA_SEARCH_KEY`, so you can read the stories afterwards! Your story's text and images will now be added to an index called `daily-llm-conversations` by default. Note that the image URLs from OpenAI's DALL-E are only valid for two hours, so if you'd like to keep them, you'll need to add some logic to save them to your own storage.

> Two additional AI service connectors -- Hugging Face and Cloudflare -- are also included but not currently recommended for production use.

# Running the demo

- Start up the bot manager. This module creates rooms and meeting tokens used by bots and by the interactive.html script. The `--debug` flag is optional below, but gives you the ability to dynamically reload your python modules if they change.
```
flask --app daily-bot-manager.py --debug run
```

Then, either open `static-pages/interactive.html` in your browser of choice or spin up an HTTP server and navigate
to the port shown in your terminal:

```
 python -m http.server --directory static-pages
```

The above should open your default browser. If your browser does not open automatically, navigate to the web-app port shown in your terminal after the final command above. Once there, the application will automatically open a Daily call with the bot joined; you can interact with the bot on this page.

- NOTE: By default the above command to launch flask will listen on `http://127.0.0.1:5000` and that path is specified in `static-pages/index.js`; if, for some reason, your flask instance is listening on a different host or port, edit this line in the file:

```
        fetch('http://127.0.0.1:5000/spin-up-bot', {
        //...
```

# More than just storytelling

You can customize the behavior of the app by looking at `orchestrator.py` and the `scenes` folder. More info on customization coming soon!

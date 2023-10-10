window.addEventListener('DOMContentLoaded', () => {
  init();
});

/**
 * Spins up the bot and accompanying LLM operations,
 * then joins a call through Daily Prebuilt
 */
function init() {
  // This is the default port when running the `daily-bot-manager.py` Flask app.
  // If your bot manager is running on a different port, modify it below.
  fetch('http://127.0.0.1:5000/spin-up-bot', {
    method: 'POST',
  })
    .then((res) => {
      if (!res.ok) {
        res.text().then((text) => {
          console.error(
            'failed to spin up bot:',
            res.status,
            res.statusText,
            text,
          );
        });
        return null;
      }
      return res.json();
    })
    .then((data) => {
      const call = createCallObject();
      join(call, data.room_url, data.token);
    })
    .catch((e) => console.error('failed to spin up bot', e));
}

/**
 * Creates a Daily Prebuilt call frame and configures
 * relevant Daily event listeners.
 * @returns {DailyCall}
 */
function createCallObject() {
  const call = window.DailyIframe.createFrame({
    showLeaveButton: true,
    iframeStyle: {
      position: 'fixed',
      top: '0',
      left: '0',
      width: '100%',
      height: '100%',
    },
  });
  window.call = call;

  call
    .on('joined-meeting', () => {
      // watchdog timer in case the bot never joins
      setTimeout(async () => {
        const pax = call.participants();
        console.log({ pax });
        if (Object.keys(pax).length === 1) {
          window.alert(
            "Sorry! It looks like all of our bots are busy right now. Please use your browser's Back button to go back to the previous page, and click the button to try again.",
          );
        }
      }, 10 * 1000);
    })
    .on('transcription-started', () => console.log('transcription started'))
    .on('left-meeting', () => {
      readStory(window.storyID);
    })
    .on('app-message', (msg) => {
      // if it's a transcription chunk of the current user's audio
      console.log('🎙️ app message received', msg);
      if (msg.fromId === 'transcription') {
        call.sendAppMessage({
          event: 'transcription-ready',
          text: msg.data.text,
        });
      }

      if (msg.data.event === 'story-id') {
        // redirect to the story page in 10 minutes
        window.storyID = msg.data.storyID;

        setTimeout(
          () => {
            readStory(window.storyID);
          },
          1000 * 60 * 10,
        );
      }
    });
  return call;
}

/**
 * Joins the given Daily room
 * @param call DailyCall
 * @param roomURL string
 * @param token string
 */
function join(call, roomURL, token) {
  call.join({
    url: roomURL,
    token,
  });
}

function readStory() {
  window.location.href = `read.html?storyID=${window.storyID}`;
}

import os
import requests
import subprocess
import time

from flask import Flask, jsonify
from flask_cors import CORS
from auth import get_meeting_token

app = Flask(__name__)
CORS(app)

@app.route('/spin-up-bot', methods=['POST'])
def spin_up_bot():
    daily_api_key = os.getenv('DAILY_API_KEY')
    api_path = os.getenv('DAILY_API_PATH') or 'https://api.daily.co/v1'

    timeout = int(os.getenv("BOT_MAX_DURATION") or 300)
    exp = time.time() + timeout
    res = requests.post(f'{api_path}/rooms',
                        headers={'Authorization': f'Bearer {daily_api_key}'},
                        json={
                            'properties': {
                                'exp': exp,
                                'enable_chat':True,
                                'enable_emoji_reactions': True,
                                'eject_at_room_exp': True,
                                'enable_prejoin_ui': False,
                            }
                        })
    if res.status_code != 200:
        return jsonify({'error': 'Unable to create room', 'status_code': res.status_code, 'text': res.text}), 500
    room_url = res.json()['url']
    room_name = res.json()['name']

    meeting_token = get_meeting_token(room_name, daily_api_key, exp)

    proc = subprocess.Popen([f'python ./daily-llm.py -u {room_url} -t {meeting_token}'], shell=True, bufsize=1)

    # Don't return until the bot has joined the room, but wait for at most 2 seconds.
    attempts = 0
    while attempts < 20:
        time.sleep(0.1)
        attempts += 1
        res = requests.get(f"{api_path}/rooms/{room_name}/get-session-data", headers={'Authorization': f'Bearer {daily_api_key}'})
        if res.status_code == 200:
            break
    print(f"Took {attempts} attempts to join room {room_name}")

    return jsonify({'room_url': room_url, 'token': meeting_token}), 200

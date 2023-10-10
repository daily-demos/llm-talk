import os
import requests
import subprocess
import time

from flask import Flask, request, jsonify
from flask_cors import CORS

running_bots = []

app = Flask(__name__)
CORS(app)

@app.route('/spin-up-bot', methods=['POST'])
def spin_up_bot():
    daily_api_key = os.getenv('DAILY_API_KEY')
    api_path = os.getenv('DAILY_API_PATH') or 'https://api.daily.co/v1'

    timeout = int(os.getenv("BOT_MAX_DURATION") or 300)
    res = requests.post(f'{api_path}/rooms',
                        headers={'Authorization': f'Bearer {daily_api_key}'},
                        json={
                            'properties': {
                                'exp': time.time() + timeout,
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

    res = requests.post(f'{api_path}/meeting-tokens',
                        headers={'Authorization': f'Bearer {daily_api_key}'},
                        json={'properties': {'room_name': room_name, 'is_owner': True}})
    if res.status_code != 200:
        return jsonify({'error': 'Unable to create meeting token', 'detail': res.text}), 500
    meeting_token = res.json()['token']

    proc = subprocess.Popen([f'python ./daily-llm.py -u {room_url} -t {meeting_token}'], shell=True, bufsize=1)
    running_bots.append([proc.pid, room_url, meeting_token])

    return jsonify({'room_url': room_url, 'token': meeting_token}), 200


@app.route('/bots', methods=['GET'])
def get_bots():
    return jsonify({'bots': running_bots}), 200

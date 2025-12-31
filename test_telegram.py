import json
import requests
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, 'config.json')

def load_config():
    with open(CONFIG_PATH, 'r', encoding='utf-8-sig') as f:
        return json.load(f)

def test_telegram():
    config = load_config()
    token = config.get('telegram_bot_token')
    chat_id = config.get('telegram_chat_id')
    
    print(f"Token: {token}")
    print(f"Chat ID: {chat_id}")

    if not token or 'YOUR_' in token:
        print("Error: Token is not set correctly.")
        return

    msg = "✅ Test Message from Job Bot. If you see this, your configuration is correct!"
    url = f'https://api.telegram.org/bot{token}/sendMessage'
    payload = {'chat_id': chat_id, 'text': msg}
    
    try:
        print(f"Sending request to {url}...")
        resp = requests.post(url, json=payload, timeout=10)
        print(f"Status Code: {resp.status_code}")
        print(f"Response: {resp.text}")
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == '__main__':
    test_telegram()

import random
import time
import requests

URL = 'http://localhost:8000/vitals/'

# user Token
USER_TOKEN = ''
DEVICE_ID = 'ESP32-1001'

headers = {'Authorization': f'Token {USER_TOKEN}'}

for i in range(1, 51):
  heart_rate = random.randint(60, 100)
  oxygen_level = random.randint(95, 99)

  payload = {
      'device': 22,
      'heart_rate': heart_rate,
      'oxygen_level': oxygen_level,
  }

  try:
    response = requests.post(URL, json=payload, headers=headers)
    print(f'[{i}/50] Status: {response.status_code} | Data: {payload}')
    if response.status_code not in (200, 201):
      print(f'    Error details: {response.text}')
  except Exception as e:
    print(f'Connection failed: {e}')

  time.sleep(1)
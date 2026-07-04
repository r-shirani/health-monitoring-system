import requests, random, time
#local Address
url_address = 'http://127.0.0.1:8000/vitals/'

admin_token = 'Token 4319a69e17510dd61229579d803570dec26575da'

vitals = {}

#create random data
for i in range(200):
    heart_rate = random.randint(40, 150)
    oxygen_level = random.randint(80, 100)

    vitals = {'device': '1', 'heart_rate': heart_rate, 'oxygen_level': oxygen_level}

    result = requests.post(url=url_address, json=vitals, headers={'Authorization':admin_token})

    print(f'request {i}: {result.status_code}') #print the request status code to make sure requests are sent to the server

    time.sleep(1) # sleep for one sec to be more similar to the actual device
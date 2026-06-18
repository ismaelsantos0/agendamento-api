import urllib.request
import urllib.parse
import json

url = 'https://agendamentos01-production.up.railway.app/auth/token'
data = urllib.parse.urlencode({'username': 'master', 'password': 'change-me-immediately'}).encode('utf-8')
req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/x-www-form-urlencoded'})
try:
    with urllib.request.urlopen(req) as response:
        token = json.loads(response.read().decode())['access_token']
        print('Got token')
        
        # Now get professionals
        req2 = urllib.request.Request('https://agendamentos01-production.up.railway.app/professionals', headers={'Authorization': 'Bearer ' + token})
        with urllib.request.urlopen(req2) as resp2:
            profs = json.loads(resp2.read().decode())
            print('Profs:', profs)
            
            if profs:
                prof_id = profs[0]['id']
                payload = json.dumps({'professional_id': prof_id, 'day_of_week': 1, 'start_time': '09:00:00', 'end_time': '18:00:00'}).encode('utf-8')
                req3 = urllib.request.Request('https://agendamentos01-production.up.railway.app/availability', data=payload, headers={'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json'})
                with urllib.request.urlopen(req3) as resp3:
                    print('Create rule response:', resp3.read().decode())
except urllib.error.HTTPError as e:
    print('HTTPError:', e.code, e.read().decode())
except Exception as e:
    print('Error:', str(e))

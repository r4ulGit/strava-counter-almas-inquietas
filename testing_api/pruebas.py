import requests

# --- Configuración ---
client_id = '184167'
client_secret = '873e9ab50d3315c172338512175dfbf3988bb9b3'
refresh_token = '3ac758488a082c57039ed2b4cc09b0e513c7e640'
club_id = 1793883

def refresh_access_token():
    resp = requests.post(
        'https://www.strava.com/oauth/token',
        data={
            'client_id': client_id,
            'client_secret': client_secret,
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token,
        }
    )
    if resp.status_code == 200:
        data = resp.json()
        print("Token renovado correctamente")
        return data['access_token'], data['refresh_token']
    else:
        print('Fallo al renovar token:', resp.text)
        return None, None
    
# Renovar el token si es necesario (opcional)
access_token, refresh_token = refresh_access_token()

redirect_uri = 'https://tudominio.com/callback'  # pon tu URL de callback aquí

scopes = "activity:read,activity:read_all,profile:read_all"
auth_url = (
    f"https://www.strava.com/oauth/authorize?"
    f"client_id={client_id}&response_type=code"
    f"&redirect_uri={redirect_uri}&scope={scopes}&approval_prompt=force"
)
print(auth_url)


url = f'https://www.strava.com/api/v3/clubs/{club_id}/activities'
headers = {'Authorization': f'Bearer {access_token}'}
params = {'per_page': 50, 'page': 1}  # Modifica per_page si hay más de 50 miembros

response = requests.get(url, headers=headers, params=params)
if response.status_code == 200:
    import json
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))
else:
    print('Error:', response.status_code, response.text)

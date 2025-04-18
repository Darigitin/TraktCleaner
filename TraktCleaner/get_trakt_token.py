import requests
import json

# --- Fill these out from your Trakt App ---
CLIENT_ID = '1663abd66b1e1353a63f1d404f79611f7be0af309dff2521a557dde393f5be98'
CLIENT_SECRET = 'a4d0c3037d8180da42e66c080989519f0f2a153e29b0ccb4fdf6e2fd29891cb0'
REDIRECT_URI = 'urn:ietf:wg:oauth:2.0:oob'
# ------------------------------------------

# Step 1: Ask user to input their authorization code
auth_code = input("Paste your Trakt Authorization Code here: ").strip()

# Step 2: Set up the token request payload
payload = {
    'code': auth_code,
    'client_id': CLIENT_ID,
    'client_secret': CLIENT_SECRET,
    'redirect_uri': REDIRECT_URI,
    'grant_type': 'authorization_code'
}

# Step 3: Send POST request to Trakt to get the access token
response = requests.post('https://api.trakt.tv/oauth/token', json=payload)

# Step 4: Handle the response
if response.status_code == 200:
    data = response.json()
    print("\n✅ Access Token:")
    print(data['access_token'])
    print("\n(You can paste this into your .env file!)")
else:
    print("\n❌ Something went wrong:")
    print(f"Status Code: {response.status_code}")
    print(response.text)

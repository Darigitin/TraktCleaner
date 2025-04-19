import requests
import json

# --- Fill these out from your Trakt App ---
CLIENT_ID = ''
CLIENT_SECRET = ''
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

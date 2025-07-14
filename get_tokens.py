from google_auth_oauthlib.flow import InstalledAppFlow
import pickle  # or use json if you prefer

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

# Create the flow
flow = InstalledAppFlow.from_client_secrets_file(
    'credentials.json', SCOPES)

# Run the authorization flow
creds = flow.run_local_server(port=0)

# Save the tokens to a file
with open('token.pickle', 'wb') as token_file:
    pickle.dump(creds, token_file)

print("Access Token:", creds.token)
print("Refresh Token:", creds.refresh_token)
print("Tokens saved to token.pickle ✅")

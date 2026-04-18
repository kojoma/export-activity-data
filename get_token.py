from stravalib.client import Client

client_id = 'STRAVA_CLIENT_ID'
client_secret = 'STRAVA_CLIENT_SECRET'
code = 'STRAVA_AUTH_CODE'

client = Client()
token_response = client.exchange_code_for_token(
    client_id=client_id,
    client_secret=client_secret,
    code=code
)

print("\n--- 成功！以下の情報をコピーして GitHub Secrets に保存してください ---")
print(f"STRAVA_REFRESH_TOKEN: {token_response['refresh_token']}")
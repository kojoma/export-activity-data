from stravalib.client import Client

client_id = 'STRAVA_CLIENT_ID'

client = Client()
url = client.authorization_url(
    client_id=client_id,
    redirect_uri='http://localhost',
    scope=['read_all', 'profile:read_all', 'activity:read_all']
)

print(f"\n1. ブラウザで以下のURLにアクセスしてください:\n{url}")
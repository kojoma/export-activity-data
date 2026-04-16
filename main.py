import os
import json
import base64
from datetime import datetime, timedelta
from garminconnect import Garmin

# 一時的にトークンを置くパス
TOKEN_DIR = "session"
TOKEN_PATH = os.path.join(TOKEN_DIR, "garmin_tokens")

def main():
    email = os.getenv("GARMIN_EMAIL")
    password = os.getenv("GARMIN_PASSWORD")
    token_base64 = os.getenv("GARMIN_TOKENS_BASE64") # Secretsから取得

    if not email or not password:
        print("Error: GARMIN_EMAIL or GARMIN_PASSWORD not set.")
        return

    os.makedirs(TOKEN_DIR, exist_ok=True)
    client = Garmin(email, password)

    # --- ログイン処理 ---
    try:
        if token_base64:
            # Secretsから受け取ったBase64文字列をデコードしてファイルに書き出し
            print("Using tokens from environment variable...")
            token_data = base64.b64decode(token_base64)
            # garminconnect(garth)はディレクトリを要求するため、一時的に書き出す
            with open(TOKEN_PATH, "wb") as f:
                f.write(token_data)
            client.login(TOKEN_PATH)
        else:
            print("No tokens found in environment. Logging in with credentials...")
            client.login()
            # ログイン成功後、新しいトークンを保存して表示（初回用）
            client.garth.dump(TOKEN_PATH)

            # GitHub Secretsに貼り付けやすいようにBase64で出力
            with open(TOKEN_PATH, "rb") as f:
                new_token_base64 = base64.b64encode(f.read()).decode("utf-8")
            print("\n!!! ATTENTION: COPY THE TOKEN BELOW AND SAVE TO GITHUB SECRETS !!!")
            print(f"Name: GARMIN_TOKENS_BASE64")
            print(f"Value: {new_token_base64}")
            print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n")

    except Exception as e:
        print(f"Login failed: {e}")
        return

    # --- データ取得処理（期間指定：直近7日） ---
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)

        activities = client.get_activities_by_date(
            start_date.strftime("%Y-%m-%d"),
            end_date.strftime("%Y-%m-%d")
        )

        all_activity_data = []
        for activity in activities:
            activity_id = activity["activityId"]
            print(f"Fetching: {activity['startTimeLocal']} - {activity['activityName']}")

            splits_data = client.get_activity_splits(activity_id)

            all_activity_data.append({
                "activity_id": activity_id,
                "name": activity["activityName"],
                "start_time": activity["startTimeLocal"],
                "type": activity["activityType"]["typeKey"],
                "total_distance_m": activity["distance"],
                "total_duration_sec": activity["duration"],
                "laps": splits_data.get("entries", [])
            })

        # JSON出力
        output_filename = f"data/activity_{end_date.strftime('%Y%m%d')}.json"
        os.makedirs("data", exist_ok=True)
        with open(output_filename, "w", encoding="utf-8") as f:
            json.dump(all_activity_data, f, ensure_ascii=False, indent=2)

        print(f"Success! Saved to {output_filename}")

    except Exception as e:
        print(f"Data fetch error: {e}")

if __name__ == "__main__":
    main()

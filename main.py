import os
import json
from datetime import datetime, timedelta
from garminconnect import Garmin

def main():
    # 1. 環境変数から認証情報を取得 (GitHub Secrets用)
    email = os.getenv("GARMIN_EMAIL")
    password = os.getenv("GARMIN_PASSWORD")
    
    if not email or not password:
        print("Error: GARMIN_EMAIL or GARMIN_PASSWORD not set.")
        return

    try:
        # 2. Garmin Connectにログイン
        client = Garmin(email, password)
        client.login()
        print("Login successful.")

        # 3. 取得期間の設定 (例: 直近7日間)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        # アクティビティ一覧を取得
        activities = client.get_activities_by_date(
            start_date.strftime("%Y-%m-%d"), 
            end_date.strftime("%Y-%m-%d")
        )

        all_activity_data = []

        for activity in activities:
            activity_id = activity["activityId"]
            activity_name = activity["activityName"]
            start_time = activity["startTimeLocal"]
            
            print(f"Fetching details for: {start_time} - {activity_name}")

            # 4. 詳細データ（ラップ情報）の取得
            # splits情報が含まれる詳細データを取得
            splits_data = client.get_activity_splits(activity_id)
            
            activity_summary = {
                "activity_id": activity_id,
                "name": activity_name,
                "start_time": start_time,
                "type": activity["activityType"]["typeKey"],
                "total_distance_m": activity["distance"],
                "total_duration_sec": activity["duration"],
                "laps": splits_data.get("entries", [])
            }
            all_activity_data.append(activity_summary)

        # 5. JSONファイルとして保存
        output_filename = f"data/activity_{end_date.strftime('%Y%m%d')}.json"
        os.makedirs("data", exist_ok=True)
        
        with open(output_filename, "w", encoding="utf-8") as f:
            json.dump(all_activity_data, f, ensure_ascii=False, indent=2)
            
        print(f"Success! Saved to {output_filename}")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()

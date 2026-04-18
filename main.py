import os
import json
from datetime import datetime, timedelta
from stravalib.client import Client

def main():
    client_id = os.getenv("STRAVA_CLIENT_ID")
    client_secret = os.getenv("STRAVA_CLIENT_SECRET")
    refresh_token = os.getenv("STRAVA_REFRESH_TOKEN")

    if not all([client_id, client_secret, refresh_token]):
        print("Error: Strava credentials not set in environment variables.")
        return

    client = Client()

    # アクセストークンの更新
    token_response = client.refresh_access_token(
        client_id=client_id,
        client_secret=client_secret,
        refresh_token=refresh_token
    )
    client.access_token = token_response['access_token']

    # 直近7日間のアクティビティを取得
    after = datetime.now() - timedelta(days=7)
    activities = client.get_activities(after=after)

    all_activity_data = []

    for activity in activities:
        # ランニング以外はスキップ
        if activity.type != 'Run':
            continue

        print(f"Fetching details for: {activity.start_date_local} - {activity.name}")

        # 詳細データとラップ情報を取得
        full_activity = client.get_activity(activity.id)
        laps = client.get_activity_laps(activity.id)

        activity_summary = {
            "activity_id": activity.id,
            "name": activity.name,
            "start_time": activity.start_date_local.isoformat(),
            "distance_m": float(activity.distance),
            "moving_time_sec": activity.moving_time.total_seconds(),
            "average_heartrate": getattr(activity, 'average_heartrate', None),
            "average_speed_m_per_s": float(activity.average_speed),
            "average_cadence": getattr(activity, 'average_cadence', None),
            # ランニングダイナミクス系（Stravaにデータがある場合のみ）
            "average_stride_length": getattr(full_activity, 'average_step_length', None),
            "average_vertical_oscillation": getattr(full_activity, 'average_vertical_oscillation', None),
            "average_stance_time": getattr(full_activity, 'average_stance_time', None),
            "laps": []
        }

        for lap in laps:
            activity_summary["laps"].append({
                "lap_index": lap.lap_index,
                "distance_m": float(lap.distance),
                "total_elevation_gain_m": float(lap.total_elevation_gain),
                "average_speed_m_per_s": float(lap.average_speed),
                "average_heartrate": getattr(lap, 'average_heartrate', None)
            })

        all_activity_data.append(activity_summary)

    # JSONファイルとして保存
    os.makedirs("data", exist_ok=True)
    output_filename = f"data/strava_activity_{datetime.now().strftime('%Y%m%d')}.json"

    with open(output_filename, "w", encoding="utf-8") as f:
        json.dump(all_activity_data, f, ensure_ascii=False, indent=2)

    print(f"Success! Saved {len(all_activity_data)} activities to {output_filename}")

if __name__ == "__main__":
    main()
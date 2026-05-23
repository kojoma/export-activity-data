import os
import json
from datetime import datetime, timedelta
from stravalib.client import Client

def m_per_s_to_pace(m_per_s):
    if not m_per_s or m_per_s == 0:
        return None
    pace_min_per_km = 16.6667 / m_per_s
    minutes = int(pace_min_per_km)
    seconds = int((pace_min_per_km - minutes) * 60)
    return f"{minutes}:{seconds:02d}"

def main():
    client_id = os.getenv("STRAVA_CLIENT_ID")
    client_secret = os.getenv("STRAVA_CLIENT_SECRET")
    refresh_token = os.getenv("STRAVA_REFRESH_TOKEN")

    client = Client()
    token_response = client.refresh_access_token(
        client_id=client_id,
        client_secret=client_secret,
        refresh_token=refresh_token
    )
    client.access_token = token_response['access_token']

    # 直近7日間を対象
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)
    activities = client.get_activities(after=start_date)

    all_activity_data = []

    # 実際のアクティビティの中での最古・最新の日付をファイル名に使うための初期値
    earliest_date = end_date
    latest_date = start_date

    for activity in activities:
        if activity.type != 'Run':
            continue

        local_start = activity.start_date_local
        if local_start < earliest_date: earliest_date = local_start
        if local_start > latest_date: latest_date = local_start

        laps = client.get_activity_laps(activity.id)

        activity_summary = {
            "activity_id": activity.id,
            "name": activity.name,
            "start_time": local_start.isoformat(),
            "distance_km": round(float(activity.distance) / 1000, 2),
            "moving_time_sec": activity.moving_time.total_seconds(),
            "average_pace": m_per_s_to_pace(float(activity.average_speed)),
            "average_heartrate": getattr(activity, 'average_heartrate', None),
            "average_cadence": getattr(activity, 'average_cadence', None),
            "laps": []
        }

        for lap in laps:
            activity_summary["laps"].append({
                "lap_index": lap.lap_index,
                "distance_m": float(lap.distance),
                "total_elevation_gain_m": float(lap.total_elevation_gain),
                "average_pace": m_per_s_to_pace(float(lap.average_speed)),
                "average_heartrate": getattr(lap, 'average_heartrate', None)
            })

        all_activity_data.append(activity_summary)

    if not all_activity_data:
        print("No run activities found in the last 7 days.")
        return

    # ファイル名: activities_20260411_20260418.json のような形式
    os.makedirs("data", exist_ok=True)
    file_range = f"{earliest_date.strftime('%Y%m%d')}_{latest_date.strftime('%Y%m%d')}"
    output_filename = f"data/activities_{file_range}.json"

    with open(output_filename, "w", encoding="utf-8") as f:
        json.dump(all_activity_data, f, ensure_ascii=False, indent=2)

    print(f"Success! Saved to {output_filename}")

if __name__ == "__main__":
    main()
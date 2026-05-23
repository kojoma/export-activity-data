import sys
import pytest
from unittest.mock import MagicMock, mock_open
from datetime import datetime

# テスト対象の関数と定数をインポート
from main import (
    m_per_s_to_pace,
    get_strava_client,
    fetch_run_activities,
    format_activity_data,
    save_to_json,
    M_PER_S_TO_MIN_PER_KM_FACTOR
)

def test_m_per_s_to_pace_valid():
    # 正常系: 2.5 m/s -> 6:40
    # 1000 / 60 / 2.5 = 16.6667 / 2.5 = 6.6667 min/km
    # 0.6667 * 60 = 40 sec -> 6:40
    assert m_per_s_to_pace(2.5) == "6:40"
    
    # 3.0 m/s -> 5:33
    # 16.6667 / 3.0 = 5.5556 min/km
    # 0.5556 * 60 = 33.3 sec -> 5:33
    assert m_per_s_to_pace(3.0) == "5:33"

def test_m_per_s_to_pace_invalid_or_zero():
    assert m_per_s_to_pace(0) is None
    assert m_per_s_to_pace(None) is None

def test_get_strava_client_success(mocker):
    # Client クラスをモック化
    mock_client_class = mocker.patch("main.Client")
    mock_client_instance = mock_client_class.return_value
    
    # refresh_access_token の振る舞いを定義
    mock_client_instance.refresh_access_token.return_value = {
        "access_token": "mocked_access_token"
    }

    client = get_strava_client("id", "secret", "token")
    
    # メソッド呼び出しとアクセストークンの設定を検証
    mock_client_instance.refresh_access_token.assert_called_once_with(
        client_id="id",
        client_secret="secret",
        refresh_token="token"
    )
    assert client.access_token == "mocked_access_token"

def test_get_strava_client_failure(mocker):
    mock_client_class = mocker.patch("main.Client")
    mock_client_instance = mock_client_class.return_value
    mock_client_instance.refresh_access_token.side_effect = Exception("API Error")

    # 例外時に sys.exit(1) が呼ばれることを検証
    with pytest.raises(SystemExit) as exc_info:
        get_strava_client("id", "secret", "token")
    
    assert exc_info.value.code == 1

def test_fetch_run_activities_success(mocker):
    mock_client = MagicMock()
    mock_client.get_activities.return_value = ["activity1", "activity2"]

    start_date = datetime(2026, 5, 1)
    activities = fetch_run_activities(mock_client, start_date)

    mock_client.get_activities.assert_called_once_with(after=start_date)
    assert activities == ["activity1", "activity2"]

def test_fetch_run_activities_failure(mocker):
    mock_client = MagicMock()
    mock_client.get_activities.side_effect = Exception("Fetch Error")

    with pytest.raises(SystemExit) as exc_info:
        fetch_run_activities(mock_client, datetime.now())
    
    assert exc_info.value.code == 1

def test_format_activity_data_success(mocker):
    mock_client = MagicMock()
    
    # モックの Lap オブジェクト
    mock_lap = MagicMock()
    mock_lap.lap_index = 1
    mock_lap.distance = 1000.0
    mock_lap.total_elevation_gain = 10.0
    mock_lap.average_speed = 3.0
    mock_lap.average_heartrate = 150.0

    mock_client.get_activity_laps.return_value = [mock_lap]

    # モックの Activity オブジェクト
    mock_activity = MagicMock()
    mock_activity.id = 12345
    mock_activity.name = "Morning Run"
    mock_activity.start_date_local = datetime(2026, 5, 23, 9, 0, 0)
    mock_activity.distance = 5000.0
    mock_activity.moving_time.total_seconds.return_value = 1500.0
    mock_activity.average_speed = 3.3333  # 5:00 / km
    mock_activity.average_heartrate = 145.0
    mock_activity.average_cadence = 90.0  # 片足 90 RPM

    result = format_activity_data(mock_client, mock_activity)

    assert result is not None
    assert result["activity_id"] == 12345
    assert result["name"] == "Morning Run"
    assert result["start_time"] == "2026-05-23T09:00:00"
    assert result["distance_km"] == 5.0
    assert result["moving_time_sec"] == 1500.0
    assert result["average_pace"] == "5:00"
    assert result["average_heartrate"] == 145.0
    assert result["average_cadence"] == 180.0  # 両足 180 SPM

    # ラップ情報の検証
    assert len(result["laps"]) == 1
    assert result["laps"][0]["lap_index"] == 1
    assert result["laps"][0]["distance_m"] == 1000.0
    assert result["laps"][0]["total_elevation_gain_m"] == 10.0
    assert result["laps"][0]["average_pace"] == "5:33"
    assert result["laps"][0]["average_heartrate"] == 150.0

def test_format_activity_data_with_none_values(mocker):
    mock_client = MagicMock()
    
    # None 値が含まれるモックの Lap オブジェクト
    mock_lap = MagicMock()
    mock_lap.lap_index = 1
    mock_lap.distance = None
    mock_lap.total_elevation_gain = None
    mock_lap.average_speed = None
    mock_lap.average_heartrate = None

    mock_client.get_activity_laps.return_value = [mock_lap]

    # None 値が含まれるモックの Activity オブジェクト
    mock_activity = MagicMock()
    mock_activity.id = 12345
    mock_activity.name = "None Run"
    mock_activity.start_date_local = None
    mock_activity.distance = None
    mock_activity.moving_time = None
    mock_activity.average_speed = None
    mock_activity.average_heartrate = None
    mock_activity.average_cadence = None

    result = format_activity_data(mock_client, mock_activity)

    assert result is not None
    assert result["activity_id"] == 12345
    assert result["start_time"] is None
    assert result["distance_km"] == 0.0
    assert result["moving_time_sec"] == 0.0
    assert result["average_pace"] is None
    assert result["average_heartrate"] is None
    assert result["average_cadence"] is None

    assert len(result["laps"]) == 1
    assert result["laps"][0]["distance_m"] == 0.0
    assert result["laps"][0]["total_elevation_gain_m"] == 0.0
    assert result["laps"][0]["average_pace"] is None
    assert result["laps"][0]["average_heartrate"] is None

def test_format_activity_data_laps_failure(mocker):
    mock_client = MagicMock()
    mock_client.get_activity_laps.side_effect = Exception("Laps Error")

    mock_activity = MagicMock()
    mock_activity.id = 12345

    # laps の取得に失敗した場合は None を返すこと
    result = format_activity_data(mock_client, mock_activity)
    assert result is None

def test_save_to_json_success(mocker):
    # os.makedirs と open をモック化
    mocker.patch("os.makedirs")
    mock_file = mocker.patch("builtins.open", mock_open())
    mock_json_dump = mocker.patch("json.dump")

    earliest_date = datetime(2026, 5, 1)
    latest_date = datetime(2026, 5, 7)
    all_data = [{"activity_id": 1}]

    filename = save_to_json(all_data, earliest_date, latest_date)

    assert filename == "data/activities_20260501_20260507.json"
    mock_file.assert_called_once_with("data/activities_20260501_20260507.json", "w", encoding="utf-8")
    mock_json_dump.assert_called_once()

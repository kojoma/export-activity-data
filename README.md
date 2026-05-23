# export-activity-data

Strava API を使用して、自身のランニングアクティビティ（ラップ情報、心拍数、ピッチ等）を取得し、JSON 形式で履歴保存するためのツールです。GitHub Actions により、週次での自動バックアップが可能です。

## 1. セットアップ（初回のみ）

### Strava API アプリの登録
1. [Strava Developers](https://www.strava.com/settings/api) にアクセスし、アプリケーションを登録します。
2. **Authorization Callback Domain** には `localhost` と入力してください。
3. 発行された **Client ID** と **Client Secret** を控えておきます。

### 認証トークンの取得
Strava API は公式の OAuth2 認証が必要です。以下の手順で永続的なリフレッシュトークンを取得します。

1. **認可URLの生成**
   `auth.py` の `client_id` を書き換え実行し、表示された URL にブラウザでアクセスして「承認」をクリックします。
   ```bash
   python auth.py
   ```
2. **認可コードの取得**
   リダイレクトされた後のブラウザのURLから、`code=xxxxxx` の部分をコピーします。
3. **リフレッシュトークンの発行**
   `get_token.py` の `client_id`, `client_secret`, `code` を書き換え実行します。
   ```bash
   python get_token.py
   ```
   表示された `STRAVA_REFRESH_TOKEN` を控えてください。

## 2. GitHub Actions の設定

GitHub リポジトリの **Settings > Secrets and variables > Actions** に以下の 3 つを登録します。

| Secret 名 | 内容 |
| :--- | :--- |
| `STRAVA_CLIENT_ID` | Strava で発行された Client ID |
| `STRAVA_CLIENT_SECRET` | Strava で発行された Client Secret |
| `STRAVA_REFRESH_TOKEN` | `get_token.py` で取得したトークン |

また、**Settings > Actions > General > Workflow permissions** で `Read and write permissions` を有効にしてください。

## 3. ローカルでの実行方法

Mac 等のローカル環境で直接実行してデータを取得する場合の手順です。

### 準備
```bash
# 仮想環境の作成と起動
python3 -m venv venv
source venv/bin/activate

# 依存ライブラリのインストール
pip install stravalib
```

### 実行
環境変数をセットした状態でスクリプトを動かします。
```bash
export STRAVA_CLIENT_ID='あなたのID'
export STRAVA_CLIENT_SECRET='あなたのSecret'
export STRAVA_REFRESH_TOKEN='あなたのToken'

python main.py
```
実行に成功すると、`data/` ディレクトリに `activities_YYYYMMDD_YYYYMMDD.json` が生成されます。

## 4. 出力データについて
本ツールはランニングアクティビティのみを対象としています。
* **基本情報**: 日時、距離(km)、平均ペース(min/km)、平均心拍数、平均ピッチ
* **ラップ情報**: 各ラップごとの距離、平均ペース、平均心拍数、獲得標高

## 5. 単体テストの実行方法

本ツールには `pytest` を使用した単体テストが同梱されています。API通信部分はモック化されているため、インターネット接続や実際のAPI認証トークンがなくても、ローカル環境で安全に動作検証が可能です。

### 準備
```bash
# 仮想環境が起動している状態でテストに必要なライブラリをインストール
pip install pytest pytest-mock
```

### 実行
```bash
# テストの実行 (詳細表示付き)
pytest test_main.py -v
```
```

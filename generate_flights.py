import os
import requests
import json
from datetime import datetime, timedelta, timezone

# --- 設定値 ---
# APIキーは環境変数から取得することを強く推奨します
AEROAPI_KEY = os.environ.get("AEROAPI_KEY")
BASE_URL = "https://api.flightaware.com/aeroapi/"
AIRPORT_ID = "RJTT"  # 羽田空港のICAOコード

# タイムゾーン設定
JST = timezone(timedelta(hours=9))
UTC = timezone.utc

# 出力ファイル名
OUTPUT_HTML_FILE = "index.html"
# ----------------

def fetch_and_generate_html():
    """
    FlightAware AeroAPIからデータを取得し、HTMLファイルを生成します。
    """
    if not AEROAPI_KEY:
        print("エラー: 環境変数 'AEROAPI_KEY' が設定されていません。")
        return

    headers = {
        "Authorization": f"Token {AEROAPI_KEY}",
        "Accept": "application/json"
    }

    # APIリクエストのパラメータを設定
    today_utc = datetime.now(JST).astimezone(UTC).strftime('%Y-%m-%d')
    endpoint = f"airports/{AIRPORT_ID}/flights/departures"
    
    params = {
        "start": today_utc, 
        "max_pages": 1,
        "type": "airline"
    }

    print(f"[{datetime.now().strftime('%H:%M:%S')}] APIリクエスト開始: {BASE_URL + endpoint}...")

    try:
        response = requests.get(BASE_URL + endpoint, headers=headers, params=params)
        response.raise_for_status() # HTTPエラーが発生した場合に例外を発生させる
        data = response.json()
        
        flights_data = []
        for flight in data.get('departures', []):
            try:
                # 時刻の変換
                scheduled_time_utc = datetime.fromisoformat(flight['scheduled_out'].replace('Z', '+00:00'))
                scheduled_time_jst = scheduled_time_utc.astimezone(JST).strftime('%H:%M')

                # データ整形
                status = flight.get('status', '情報なし')
                destination = flight['destination']['name']
                flight_number = flight.get('ident', 'N/A')

                flights_data.append({
                    'flight_number': flight_number,
                    'destination': destination,
                    'scheduled_time': scheduled_time_jst,
                    'status': status
                })
            except Exception as e:
                print(f"フライトデータの処理中にエラーが発生しました: {e}. スキップします。")
                continue

        print(f"[{datetime.now().strftime('%H:%M:%S')}] {len(flights_data)}件のフライト情報を取得しました。")
        generate_html_file(flights_data)

    except requests.exceptions.HTTPError as e:
        status_code = e.response.status_code
        try:
            error_details = e.response.json()
        except:
            error_details = {"message": e.response.text}
        
        print(f"AeroAPI HTTPエラー: ステータスコード {status_code}")
        print(f"詳細: {error_details}")
        generate_error_html(f"APIエラー: HTTP {status_code}", error_details)

    except requests.exceptions.RequestException as e:
        print(f"ネットワークエラー: {e}")
        generate_error_html("ネットワークエラー", str(e))


def generate_html_file(flights):
    """取得したフライトデータをもとにHTMLを生成し、ファイルに書き出します。"""
    
    # テーブルの行を生成
    table_rows = ""
    if not flights:
        table_rows = '<tr><td colspan="4">現在、出発予定のフライト情報はありません。</td></tr>'
    else:
        for flight in flights:
            status_class = ''
            if 'Delayed' in flight['status']:
                status_class = 'status-delayed'
            elif 'Canceled' in flight['status'] or 'Diverted' in flight['status']:
                status_class = 'status-canceled'

            table_rows += f"""
                <tr>
                    <td>{flight['flight_number']}</td>
                    <td>{flight['destination']}</td>
                    <td>{flight['scheduled_time']}</td>
                    <td class="{status_class}">{flight['status']}</td>
                </tr>
            """
            
    # HTML全体を構築
    html_content = f"""
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>羽田空港 出発便掲示板</title

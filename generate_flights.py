# generate_flights.py の一番先頭に追加
print("--- SCRIPT STARTED SUCCESSFULLY ---")
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

# generate_flights.py の修正

# ... (中略)

def fetch_and_generate_html():
    """
    FlightAware AeroAPIからデータを取得し、HTMLファイルを生成します。
    """
    if not AEROAPI_KEY:
        # キーが設定されていない場合にエラーメッセージを出力
        print("致命的エラー: 環境変数 'AEROAPI_KEY' が設定されていません。")
        generate_error_html("Secrets設定エラー", "APIキーが環境変数 'AEROAPI_KEY' に設定されていません。")
        return

    # ... (後略)
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

# generate_flights.py の修正（fetch_and_generate_html 関数内）

    try:
        response = requests.get(BASE_URL + endpoint, headers=headers, params=params, timeout=10)
        
        # ★★★ ここからデバッグ出力とエラー処理を再強化 ★★★
        
        print(f"[{datetime.now(JST).strftime('%H:%M:%S')}] APIレスポンスステータスコード: {response.status_code}")
        
        if response.status_code != 200:
            # 200以外のステータスコードの場合、本文をログに出力
            print(f"[{datetime.now(JST).strftime('%H:%M:%S')}] APIレスポンス本文 (非200): {response.text}")
            
            # APIがJSON以外のエラーを返した場合でも、HTMLファイルを生成する
            error_details = response.text 
            generate_error_html(f"APIエラー: HTTP {response.status_code}", error_details)
            return # エラー処理後、処理を終了

        # ステータスコードが200の場合、JSONを処理
        data = response.json()
        
        # ... (以下、フライトデータを処理する既存のコードを続行)
        
    except requests.exceptions.RequestException as e:
        # タイムアウトやその他のリクエストエラーの場合
        import traceback
        error_trace = traceback.format_exc() # トレースバック全体を取得
        print(f"致命的なリクエストエラーが発生しました: {e}")
        print("----- FULL TRACEBACK -----")
        print(error_trace)
        print("--------------------------")
        generate_error_html("リクエスト/接続エラー", str(e) + "\n\n" + error_trace)
        return
    except Exception as e:
        # 予期せぬエラー（JSONDecodeErrorなど）の場合
        print(f"予期せぬエラー: {e}")
        generate_error_html("予期せぬスクリプトエラー", str(e))


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
    # 修正後
    html_content = f"""
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>羽田空港 出発便掲示板</title>
    <style>
        body {{ font-family: sans-serif; margin: 20px; background-color: #f0f0f0; }}
        .board-container {{ background-color: #333; color: white; padding: 20px; border-radius: 8px; max-width: 800px; margin: 0 auto; }}
        h1 {{ text-align: center; color: #fff; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
        th, td {{ padding: 12px; border-bottom: 1px solid #555; text-align: left; }}
        th {{ background-color: #555; }}
        .status-delayed {{ color: orange; font-weight: bold; }}
        .status-canceled {{ color: red; font-weight: bold; }}
        .update-info {{ font-size: 0.9em; text-align: right; color: #ccc; margin-bottom: 10px; }}
    </style>
    <meta http-equiv="refresh" content="300"> </head>
<body>
"""

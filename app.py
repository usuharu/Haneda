import os
from flask import Flask, jsonify, render_template
import requests
from datetime import datetime, timedelta, timezone

app = Flask(__name__)

# ★★★ ここをあなたのAPI情報に置き換えてください ★★★
AEROAPI_KEY = "xf4b2A9mXA8incfSslQJTmVeMqI6P1EP"
BASE_URL = "https://api.flightaware.com/aeroapi/"
# RJTT は羽田空港のICAOコードです
AIRPORT_ID = "RJTT"

# JST (日本標準時) タイムゾーンを設定
JST = timezone(timedelta(hours=9))

@app.route('/')
def index():
    """Webサイトのメインページを表示します。"""
    return render_template('index.html')

@app.route('/api/departures')
def get_departures():
    """FlightAware AeroAPIから羽田空港の出発便データを取得します。"""
    
    headers = {
        "Authorization": f"Token {AEROAPI_KEY}",
        "Accept": "application/json"
    }

    # APIリクエストのパラメータを設定
    # todayは UTC での日付を指定する必要があるため、JSTをUTCに変換して日付を取得
    today_utc = datetime.now(JST).astimezone(timezone.utc).strftime('%Y-%m-%d')

    # 出発便のエンドポイント
    endpoint = f"airports/{AIRPORT_ID}/flights/departures"
    params = {
        "start": today_utc, # 今日の日付
        "max_pages": 1,
        "type": "airline" # 定期便のみを取得 (必要に応じて調整)
    }

    try:
        response = requests.get(BASE_URL + endpoint, headers=headers, params=params)
        response.raise_for_status() # HTTPエラーが発生した場合に例外を発生させる
        data = response.json()
        
        # 必要な情報を整形してクライアントに返す
        departures = []
        for flight in data.get('departures', []):
            try:
                # 出発予定時刻をJSTに変換して整形
                scheduled_time_utc = datetime.fromisoformat(flight['scheduled_out'])
                scheduled_time_jst = scheduled_time_utc.astimezone(JST).strftime('%H:%M')

                # 現在のステータス
                status = flight.get('status', '情報なし')

                # 行先空港名の処理 (例としてcityをそのまま使用)
                destination = flight['destination']['name']

                departures.append({
                    'flight_number': flight.get('ident'),
                    'destination': destination,
                    'scheduled_time': scheduled_time_jst,
                    'status': status
                })
            except Exception as e:
                # 個別のフライトデータの処理でエラーが発生した場合
                print(f"フライトデータの処理エラー: {e}")
                continue

        return jsonify({'flights': departures})

    except requests.exceptions.HTTPError as e:
        # HTTPステータスコードが4xxまたは5xxの場合
        status_code = e.response.status_code
        try:
            # APIからのエラーレスポンスがあれば取得
            error_details = e.response.json()
        except:
            error_details = {"message": e.response.text}

        print(f"AeroAPI HTTPエラー: ステータスコード {status_code}")
        print(f"詳細: {error_details}")

        # クライアントにもエラー情報を返す
        return jsonify({'error': f'APIエラー発生 (HTTP {status_code})', 'details': error_details}), 500

    except requests.exceptions.RequestException as e:
        # ネットワーク接続など他のエラーの場合
        print(f"AeroAPI ネットワークエラー: {e}")
        return jsonify({'error': 'ネットワーク接続エラー', 'details': str(e)}), 500

if __name__ == '__main__':
    # デバッグ用にローカルで実行
    app.run(debug=True)
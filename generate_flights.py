import os
import requests
import json
from datetime import datetime, timedelta, timezone
import traceback
from typing import List, Dict, Any

# --- APIキーの安全な取得 ---
AVIATION_STACK_KEY = None
try:
    # Colab環境の場合
    from google.colab import userdata
    AVIATION_STACK_KEY = userdata.get('AVIATION_STACK_KEY') 
except (ImportError, KeyError):
    # Colab以外の環境 (GitHub Actionsなど) の場合
    AVIATION_STACK_KEY = os.environ.get("AVIATION_STACK_KEY")
    
# --- 設定値 ---
BASE_URL = "http://api.aviationstack.com/v1/"
AIRPORT_CODE = "HND"  

# タイムゾーン設定
JST = timezone(timedelta(hours=9))
UTC = timezone.utc

# 出力ファイル名
OUTPUT_HTML_FILE = "index.html"

# --- 複数空港を持つ主要都市のリスト (英語名) ---
# このリストに含まれる都市のみ、目的地にIATAコードを付加します。
MULTI_AIRPORT_CITIES = [
    "Tokyo", "Osaka", "Nagoya", "Sapporo", # 国内
    "Shanghai", "Beijing", "Seoul", "Taipei", 
    "London", "Paris", "New York", "Chicago", "Moscow", "Milan",
    "Rome", "Kuala Lumpur", "Jakarta", "Bangkok", "Manila"
]
# ----------------

# --- 都市名の多言語マッピングテーブル（主要な都市のみ） ---
# APIが返す英語名から、日本語と中国語に変換
CITY_MAPPING = {
    "Tokyo": {"ja": "東京", "zh": "东京"},
    "Osaka": {"ja": "大阪", "zh": "大阪"},
    "Nagoya": {"ja": "名古屋", "zh": "名古屋"},
    "Sapporo": {"ja": "札幌", "zh": "札幌"},
    "Fukuoka": {"ja": "福岡", "zh": "福冈"},
    "Naha": {"ja": "那覇", "zh": "那霸"},
    "Shanghai": {"ja": "上海", "zh": "上海"},
    "Beijing": {"ja": "北京", "zh": "北京"},
    "Seoul": {"ja": "ソウル", "zh": "首尔"},
    "Taipei": {"ja": "台北", "zh": "台北"},
    "Hong Kong": {"ja": "香港", "zh": "香港"},
    "Singapore": {"ja": "シンガポール", "zh": "新加坡"},
    "Bangkok": {"ja": "バンコク", "zh": "曼谷"},
    "Kuala Lumpur": {"ja": "クアラルンプール", "zh": "吉隆坡"},
    "Manila": {"ja": "マニラ", "zh": "马尼拉"},
    "Jakarta": {"ja": "ジャカルタ", "zh": "雅加达"},
    "Sydney": {"ja": "シドニー", "zh": "悉尼"},
    "London": {"ja": "ロンドン", "zh": "伦敦"},
    "Paris": {"ja": "パリ", "zh": "巴黎"},
    # マッピングにない場合は英語名をそのまま使用
}
# ----------------

print("--- SCRIPT STARTED SUCCESSFULLY ---")

# --- HTML生成関数 ---

def generate_html_file(flights_data: List[Dict[str, str]]):
    """フライトデータからHTMLコンテンツを生成し、ファイルに書き出す"""
    
    current_time_jst = datetime.now(JST).strftime('%Y/%m/%d %H:%M:%S JST')
    
    table_rows = ""
    if not flights_data:
        # 列数が5に変更
        table_rows = '<tr><td colspan="5" style="text-align: center;">現在、出発予定のフライト情報はありません。</td></tr>'
    else:
        for flight in flights_data:
            status_class = ""
            if flight['status'] == '遅延':
                status_class = "status-delayed"
            elif flight['status'] == '欠航':
                status_class = "status-canceled"

            # 3言語のデータを td タグの data属性として埋め込む
            table_rows += f"""
                <tr>
                    <td>{flight['flight_number']}</td>
                    <td class="destination-cell" 
                        data-ja="{flight['destination_ja']}"
                        data-en="{flight['destination_en']}"
                        data-zh="{flight['destination_zh']}">
                        {flight['destination_ja']}
                    </td>
                    <td>{flight['scheduled_time']}</td>
                    <td class="{status_class}">{flight['status']}</td>
                    <td class="codeshare-cell">{flight['codeshare_flights']}</td>
                </tr>
            """

    # HTMLテンプレート
    html_content = f"""
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>羽田空港 出発便掲示板</title>
    <style>
        body {{ font-family: sans-serif; margin: 20px; background-color: #f0f0f0; }}
        .board-container {{ background-color: #333; color: white; padding: 20px; border-radius: 8px; max-width: 1000px; margin: 0 auto; }} /* 最大幅を広く */
        h1 {{ text-align: center; color: #fff; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
        th, td {{ padding: 12px; border-bottom: 1px solid #555; text-align: left; }}
        th {{ background-color: #555; }}
        .status-delayed {{ color: orange; font-weight: bold; }}
        .status-canceled {{ color: red; font-weight: bold; }}
        .update-info {{ font-size: 0.9em; text-align: right; color: #ccc; margin-bottom: 10px; }}
        .codeshare-cell {{ font-size: 0.9em; max-width: 250px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }} /* コードシェア列のスタイル */
        /* 便名と時刻の幅を固定して見やすく */
        td:nth-child(1) {{ width: 10%; }} 
        td:nth-child(3) {{ width: 10%; }}
        td:nth-child(4) {{ width: 10%; }}
        th:nth-child(5), td:nth-child(5) {{ width: 30%; }} /* コードシェア列の幅 */
    </style>
    <meta http-equiv="refresh" content="300"> 
</head>
<body>

<div class="board-container">
    <h1>羽田空港 (HND/RJTT) 出発便</h1>
    <p class="update-info">最終生成時刻: {current_time_jst}</p>

    <table>
        <thead>
            <tr>
                <th>便名</th>
                <th>行先</th>
                <th>予定時刻</th>
                <th>ステータス</th>
                <th>コードシェア便名</th>
            </tr>
        </thead>
        <tbody>
            {table_rows}
        </tbody>
    </table>
</div>

<script>
    const languages = ["ja", "en", "zh"]; // 日本語, 英語, 中国語
    let currentLangIndex = 0;
    const cells = document.querySelectorAll(".destination-cell");

    function updateLanguage() {{
        const currentLang = languages[currentLangIndex];
        
        cells.forEach(cell => {{
            const text = cell.getAttribute(`data-${{currentLang}}`);
            if (text) {{
                cell.textContent = text;
            }}
        }});
        
        currentLangIndex = (currentLangIndex + 1) % languages.length;
    }}

    // 最初に実行し、その後5秒ごとに実行
    updateLanguage(); 
    setInterval(updateLanguage, 5000); // 5秒ごとに言語を切り替え
</script>

</body>
</html>
"""
    
    try:
        with open(OUTPUT_HTML_FILE, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"[{datetime.now(JST).strftime('%H:%M:%S')}] HTMLファイル '{OUTPUT_HTML_FILE}' を正常に生成しました。")
    except Exception as e:
        print(f"HTMLファイル生成エラー: {e}")

def generate_error_html(title: str, details: str):
    """エラー発生時にエラー情報を書き込んだHTMLファイルを生成する"""
    current_time_jst = datetime.now(JST).strftime('%Y/%m/%d %H:%M:%S JST')
    
    html_content = f"""
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>エラーが発生しました</title>
    <style>
        body {{ font-family: monospace; white-space: pre-wrap; margin: 20px; background-color: #fee; color: #c00; border: 1px solid #f99; padding: 20px; }}
        pre {{ background-color: #fff; padding: 15px; border: 1px dashed #c00; overflow-x: auto; }}
    </style>
</head>
<body>
    <h1>データ取得エラー: {title}</h1>
    <p>フライト情報の取得中に深刻なエラーが発生しました。詳細は以下のログを確認してください。</p>
    <p>最終試行時刻: {current_time_jst}</p>
    <h2>詳細:</h2>
    <pre>{details}</pre>
</body>
</html>
"""
    try:
        with open(OUTPUT_HTML_FILE, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"[{datetime.now(JST).strftime('%H:%M:%S')}] エラーHTMLファイル '{OUTPUT_HTML_FILE}' を生成しました。")
    except Exception as e:
        print(f"HTMLファイル生成エラー: {e}")


# --- API呼び出しとデータ処理関数 ---

def fetch_and_generate_html():
    """
    AviationStack APIからデータを取得し、HTMLファイルを生成します。
    重複するコードシェア便を統合し、運航便名のみを表示します。
    """
    if not AVIATION_STACK_KEY:
        print("致命的エラー: AviationStackのAPIキーが設定されていません。")
        generate_error_html("Secrets設定エラー", "APIキーが環境変数/シークレットに設定されていません。")
        return

    endpoint = "flights"
    
    params = {
        "access_key": AVIATION_STACK_KEY,
        "dep_iata": AIRPORT_CODE, 
    }
    
    print(f"[{datetime.now(JST).strftime('%H:%M:%S')}] AviationStackリクエスト開始: {BASE_URL + endpoint}...")

    try:
        # ★★★ タイムアウトを15秒に延長 ★★★
        response = requests.get(BASE_URL + endpoint, params=params, timeout=15)
        
        if response.status_code != 200:
            error_details = response.text 
            generate_error_html(f"APIエラー: HTTP {response.status_code}", error_details)
            return
        
        data = response.json()
        
        # フライトをキーごとに集約するための辞書
        # キー: (予定出発時刻, 到着IATAコード) 
        aggregated_flights: Dict[tuple, Dict[str, Any]] = {}

        for flight in data.get('data', []):
            try:
                # 1. 識別キーの作成と時刻の処理
                scheduled_time_str = flight['departure']['scheduled']
                scheduled_datetime_utc = datetime.fromisoformat(scheduled_time_str.replace('Z', '+00:00'))
                
                arrival_iata = flight['arrival'].get('iata')
                flight_key = (scheduled_time_str, arrival_iata)

                # 2. 便名とコードシェアの処理
                current_flight_number = flight['flight']['iata'].upper() 
                
                # 3. 運航便名の特定
                is_operating_carrier = not flight['flight'].get('codeshared')

                if flight_key not in aggregated_flights:
                    # 新しいフライトの場合、初期化
                    
                    # 4. 行先情報の処理
                    destination_iata = arrival_iata
                    destination_city_en = flight['arrival'].get('city')
                    destination_airport_name = flight['arrival'].get('airport')
                    
                    iata_suffix = ""

                    if destination_city_en:
                        base_en = destination_city_en
                        # 複数空港を持つ都市の場合のみIATAコードを付加
                        if destination_city_en in MULTI_AIRPORT_CITIES and destination_iata:
                            iata_suffix = f" ({destination_iata})"
                    else:
                        base_en = destination_airport_name or 'N/A'
                        
                    mapped_names = CITY_MAPPING.get(base_en, {"ja": base_en, "zh": base_en})

                    destination_ja = mapped_names['ja'] + iata_suffix
                    destination_en = base_en + iata_suffix
                    destination_zh = mapped_names['zh'] + iata_suffix

                    # 5. ステータスの処理
                    status = flight['flight_status']
                    status_display = {
                        'scheduled': '予定',
                        'active': '飛行中',
                        'landed': '出発済',
                        'cancelled': '欠航',
                        'delayed': '遅延'
                    }.get(status, status)

                    aggregated_flights[flight_key] = {
                        'sort_key': scheduled_datetime_utc, 
                        'flight_number': current_flight_number if is_operating_carrier else 'TBD', 
                        'codeshares': set(), 
                        'destination_ja': destination_ja,
                        'destination_en': destination_en,
                        'destination_zh': destination_zh,
                        'scheduled_time': scheduled_datetime_utc.astimezone(JST).strftime('%H:%M'),
                        'status': status_display,
                    }

                # 既存のフライトキーの場合、情報を更新/追加
                current_agg = aggregated_flights[flight_key]

                if is_operating_carrier:
                    current_agg['flight_number'] = current_flight_number
                
                if not is_operating_carrier and current_flight_number != current_agg['flight_number']:
                    current_agg['codeshares'].add(current_flight_number)
                
                codeshare_info = flight['flight'].get('codeshared')
                if codeshare_info and codeshare_info.get('flight_iata'):
                    codeshare_iata = codeshare_info['flight_iata'].upper()
                    if codeshare_iata != current_agg['flight_number']:
                        current_agg['codeshares'].add(codeshare_iata)


            except Exception as e:
                print(f"フライトデータの処理中にエラーが発生しました: {e}. スキップします。")
                traceback.print_exc()
                continue

        # 6. 最終リストの作成とソート
        final_flights_data = []
        for flight_data in aggregated_flights.values():
            # TBDのまま残っている場合は、最も若い便名を運航便名として表示
            if flight_data['flight_number'] == 'TBD':
                if flight_data['codeshares']:
                    fallback_flight = sorted(list(flight_data['codeshares']))[0]
                    flight_data['flight_number'] = fallback_flight
                    
            # 運航便名と異なるものだけをコードシェアとして抽出
            codeshare_list = [
                c for c in flight_data['codeshares'] 
                if c != flight_data['flight_number']
            ]
            
            final_flights_data.append({
                'sort_key': flight_data['sort_key'],
                'flight_number': flight_data['flight_number'],
                'destination_ja': flight_data['destination_ja'],
                'destination_en': flight_data['destination_en'],
                'destination_zh': flight_data['destination_zh'],
                'scheduled_time': flight_data['scheduled_time'],
                'codeshare_flights': ', '.join(sorted(codeshare_list)),
                'status': flight_data['status']
            })

        # 時系列でのソート
        final_flights_data.sort(key=lambda x: x['sort_key']) 

        # ソートキーを削除してHTML生成関数に渡す
        display_flights_data = [
            {k: v for k, v in flight.items() if k != 'sort_key'}
            for flight in final_flights_data
        ]
        
        print(f"[{datetime.now(JST).strftime('%H:%M:%S')}] {len(display_flights_data)}件のフライト情報を取得しました。")
        generate_html_file(display_flights_data)

    except requests.exceptions.RequestException as e:
        error_trace = traceback.format_exc()
        print(f"致命的なリクエストエラーが発生しました: {e}")
        generate_error_html("リクエスト/接続エラー", str(e) + "\n\n" + error_trace)
        return

    except Exception as e:
        error_trace = traceback.format_exc()
        print(f"予期せぬエラー: {e}")
        generate_error_html("予期せぬスクリプトエラー", str(e) + "\n\n" + error_trace)
        return


if __name__ == "__main__":
    fetch_and_generate_html()

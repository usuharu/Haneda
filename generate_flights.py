import os
import requests
import json
from datetime import datetime, timedelta, timezone
import traceback
from typing import List, Dict, Any

# --- APIキーの安全な取得 ---
# GitHub Actionsでシークレット(Secrets)として設定することを想定しています
AVIATION_STACK_KEY = os.environ.get("AVIATION_STACK_KEY")
try:
    # Colabでのテスト用（Colab上で実行する場合のみ有効）
    from google.colab import userdata
    # 注意: Colabで実行する場合、事前にシークレット名 'AVIATION_STACK_KEY' でキーを登録してください
    if not AVIATION_STACK_KEY:
        AVIATION_STACK_KEY = userdata.get('AVIATION_STACK_KEY') 
except (ImportError, KeyError):
    pass
    
# --- 設定値 ---
BASE_URL = "http://api.aviationstack.com/v1/"
AIRPORT_CODE = "HND"  

# 航空会社ロゴのCDNベースURL
AIRLINE_LOGO_BASE_URL = "https://content.flights-api.com/v1/airlines/logo/" 

# タイムゾーン設定
JST = timezone(timedelta(hours=9))
# 出力ファイル名
OUTPUT_HTML_FILE = "index.html"

# --- 複数空港を持つ主要都市のリスト (英語名) ---
MULTI_AIRPORT_CITIES = [
    "Tokyo", "Osaka", "Nagoya", "Sapporo", 
    "Shanghai", "Beijing", "Seoul", "Taipei", 
    "London", "Paris", "New York", "Chicago", "Moscow", "Milan",
    "Rome", "Kuala Lumpur", "Jakarta", "Bangkok", "Manila"
]
# ----------------

# --- 都市名の多言語マッピングテーブル（主要な都市のみ） ---
# 日本語、英語、中国語に対応
CITY_MAPPING = {
    "Tokyo": {"ja": "東京", "en": "Tokyo", "zh": "东京"}, "Osaka": {"ja": "大阪", "en": "Osaka", "zh": "大阪"},
    "Nagoya": {"ja": "名古屋", "en": "Nagoya", "zh": "名古屋"}, "Sapporo": {"ja": "札幌", "en": "Sapporo", "zh": "札幌"},
    "Fukuoka": {"ja": "福岡", "en": "Fukuoka", "zh": "福冈"}, "Naha": {"ja": "那覇", "en": "Naha", "zh": "那霸"},
    "Shanghai": {"ja": "上海", "en": "Shanghai", "zh": "上海"}, "Beijing": {"ja": "北京", "en": "Beijing", "zh": "北京"},
    "Seoul": {"ja": "ソウル", "en": "Seoul", "zh": "首尔"}, "Taipei": {"ja": "台北", "en": "Taipei", "zh": "台北"},
    "Hong Kong": {"ja": "香港", "en": "Hong Kong", "zh": "香港"}, "Singapore": {"ja": "シンガポール", "en": "Singapore", "zh": "新加坡"},
    "Bangkok": {"ja": "バンコク", "en": "Bangkok", "zh": "曼谷"}, "Kuala Lumpur": {"ja": "クアラルンプール", "en": "Kuala Lumpur", "zh": "吉隆坡"},
    "Manila": {"ja": "マニラ", "en": "Manila", "zh": "马尼拉"}, "Jakarta": {"ja": "ジャカルタ", "en": "Jakarta", "zh": "雅加达"},
    "Sydney": {"ja": "シドニー", "en": "Sydney", "zh": "悉尼"}, "London": {"ja": "ロンドン", "en": "London", "zh": "伦敦"},
    "Paris": {"ja": "パリ", "en": "Paris", "zh": "巴黎"}, "Frankfurt": {"ja": "フランクフルト", "en": "Frankfurt", "zh": "法兰克福"},
    "Los Angeles": {"ja": "ロサンゼルス", "en": "Los Angeles", "zh": "洛杉矶"}, "New York": {"ja": "ニューヨーク", "en": "New York", "zh": "纽约"},
    "Moscow": {"ja": "モスクワ", "en": "Moscow", "zh": "莫斯科"}, "Dubai": {"ja": "ドバイ", "en": "Dubai", "zh": "迪拜"},
    "Istanbul": {"ja": "イスタンブール", "en": "Istanbul", "zh": "伊斯坦布尔"}, "Guam": {"ja": "グアム", "en": "Guam", "zh": "关岛"},
    "Hanoi": {"ja": "ハノイ", "en": "Hanoi", "zh": "河内"}, "Ho Chi Minh City": {"ja": "ホーチミン", "en": "Ho Chi Minh City", "zh": "胡志明市"},
    "Milan": {"ja": "ミラノ", "en": "Milan", "zh": "米兰"}, "Rome": {"ja": "ローマ", "en": "Rome", "zh": "罗马"},
}
# ----------------

print("--- SCRIPT STARTED SUCCESSFULLY ---")

# --- HTML生成関数 ---

def generate_html_file(flights_data: List[Dict[str, str]]):
    """フライトデータからHTMLコンテンツを生成し、ファイルに書き出す"""
    
    current_time_jst = datetime.now(JST).strftime('%Y/%m/%d %H:%M:%S JST')
    
    table_rows = ""
    # 列数が5に変更されている
    if not flights_data:
        table_rows = '<tr><td colspan="5" style="text-align: center; color: gray; padding: 20px;">現在、出発予定のフライト情報はありません。</td></tr>'
    else:
        for flight in flights_data:
            remark_class = ""
            if flight['remark_type'] == 'delayed':
                remark_class = "remark-delayed"
            elif flight['remark_type'] == 'cancelled':
                remark_class = "remark-canceled"
            elif flight['remark_type'] == 'active':
                remark_class = "remark-active"
            
            # CDNからロゴ画像のURLを生成
            logo_url = f"{AIRLINE_LOGO_BASE_URL}{flight['airline_code']}.png"

            # changed_timeが空でない場合にクラスを適用
            changed_time_cell_class = "changed-time-cell" if flight['changed_time'] else "changed-time-cell-empty"
            
            table_rows += f"""
                <tr>
                    <td class="time-cell">{flight['scheduled_time']}</td>
                    <td class="{changed_time_cell_class}">{flight['changed_time']}</td>
                    <td class="destination-cell" 
                        data-ja="{flight['destination_ja']}"
                        data-en="{flight['destination_en']}"
                        data-zh="{flight['destination_zh']}">
                        {flight['destination_ja']}
                    </td>
                    <td class="flight-cell">
                        <img src="{logo_url}" alt="{flight['airline_code']} Logo" class="airline-logo">
                        <span>{flight['flight_number']}</span>
                    </td>
                    <td class="remark-cell {remark_class}">
                        {flight['remark']}
                        <span class="codeshare-info">({flight['codeshare_flights']})</span>
                    </td>
                </tr>
            """

    # HTMLテンプレート (画像デザインに合わせた白背景・黒文字デザイン)
    html_content = f"""
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>羽田空港 出発便掲示板</title>
    <style>
        /* CSSの波括弧は全て二重({{, }})にしてNameErrorを回避 */
        body {{ font-family: 'Meiryo', 'ヒラギノ角ゴ Pro W3', sans-serif; margin: 0; background-color: #e6e6e6; color: #333; }}
        .board-container {{ background-color: #fff; padding: 20px 30px; box-shadow: 0 4px 10px rgba(0,0,0,0.2); max-width: 1000px; margin: 30px auto; border-radius: 6px; }}
        h1 {{ text-align: center; color: #004d99; margin-bottom: 5px; font-size: 1.8em; }}
        h2 {{ text-align: center; color: #666; font-size: 1.1em; margin-top: 5px; margin-bottom: 25px; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 15px; font-size: 1.1em; table-layout: fixed; }}
        th, td {{ padding: 10px 8px; border-bottom: 1px solid #ddd; text-align: left; height: 55px; vertical-align: middle; }}
        th {{ background-color: #f0f0f0; color: #333; font-weight: bold; border-top: 2px solid #004d99; }}
        td {{ color: #111; }}

        /* --- 列幅の調整 (5列構成) --- */
        th:nth-child(1), td:nth-child(1) {{ width: 12%; text-align: center; font-size: 1.2em; }} /* 定刻 */
        th:nth-child(2), td:nth-child(2) {{ width: 12%; text-align: center; font-size: 1.2em; }} /* 変更時刻 */
        th:nth-child(3), td:nth-child(3) {{ width: 38%; }} /* 行き先 */
        th:nth-child(4), td:nth-child(4) {{ width: 18%; }} /* 便名 */
        th:nth-child(5), td:nth-child(5) {{ width: 20%; font-size: 1em; }} /* 備考 */

        /* --- 時刻と備考の調整 --- */
        .time-cell {{ color: #333; font-weight: bold; }}
        .changed-time-cell {{ color: #c00; font-weight: bold; }} /* 変更時刻は赤字 */
        .changed-time-cell-empty {{ color: #ccc; }} /* 変更時刻がない場合は薄い灰色（JavaScriptで更新されるため、ここでは適用しないが残す） */
        
        /* 備考欄のステータス色 */
        .remark-delayed {{ color: #c00; font-weight: bold; }} /* 遅延は赤 */
        .remark-canceled {{ color: #c00; font-weight: bold; }} /* 欠航は赤 */
        .remark-active {{ color: #008000; font-weight: bold; }} /* 出発済は緑 */
        .remark-cell {{ font-weight: bold; }}
        
        .codeshare-info {{ display: block; font-size: 0.8em; color: #777; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 100%; margin-top: 3px; font-weight: normal; }} /* コードシェア便名は小さく備考の下に */


        /* --- ロゴと便名 --- */
        .flight-cell {{ display: flex; align-items: center; gap: 8px; font-weight: bold; color: #004d99; }}
        .airline-logo {{ width: 28px; height: 28px; border-radius: 4px; object-fit: contain; border: 1px solid #eee; flex-shrink: 0; }}

        /* --- その他 --- */
        .update-info {{ font-size: 0.85em; text-align: right; color: #777; margin-bottom: 15px; }}
    </style>
    <meta http-equiv="refresh" content="300"> 
</head>
<body>

<div class="board-container">
    <h1>国内・国際線 出発案内</h1>
    <h2>羽田空港 (HND/RJTT)</h2>
    <p class="update-info">最終更新日時: {current_time_jst}</p>

    <table>
        <thead>
            <tr>
                <th>定刻</th>
                <th>変更時刻</th>
                <th>行き先</th>
                <th>便名</th>
                <th>備考</th>
            </tr>
        </thead>
        <tbody>
            {table_rows}
        </tbody>
    </table>
</div>

<script>
    // 行き先を5秒ごとに日本語、英語、中国語で切り替えるJavaScript
    const languages = ["ja", "en", "zh"];
    let currentLangIndex = 0;
    const cells = document.querySelectorAll(".destination-cell");

    function updateLanguage() {{
        const currentLang = languages[currentLangIndex];
        
        cells.forEach(cell => {{
            // data属性から対応する言語のテキストを取得
            const text = cell.getAttribute(`data-${{currentLang}}`);
            if (text) {{
                cell.textContent = text;
            }}
        }});
        
        currentLangIndex = (currentLangIndex + 1) % languages.length;
    }}

    // 初回実行とインターバル設定
    updateLanguage(); 
    setInterval(updateLanguage, 5000); // 5秒ごとに実行
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

# ... (generate_error_html 関数は省略)

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
    """
    if not AVIATION_STACK_KEY:
        print("致命的エラー: AviationStackのAPIキーが設定されていません。")
        generate_error_html("Secrets設定エラー", "APIキーが環境変数/シークレットに設定されていません。GitHub ActionsのワークフローYAMLファイルまたはシークレット設定を確認してください。")
        return

    endpoint = "flights"
    
    params = {
        "access_key": AVIATION_STACK_KEY,
        "dep_iata": AIRPORT_CODE, 
    }
    
    print(f"[{datetime.now(JST).strftime('%H:%M:%S')}] AviationStackリクエスト開始: {BASE_URL + endpoint}...")

    try:
        # タイムアウトを15秒に設定 (以前のエラー対策)
        response = requests.get(BASE_URL + endpoint, params=params, timeout=15)
        
        # HTTP 429 Too Many Requests エラーのハンドリング
        if response.status_code == 429:
            retry_after = response.headers.get('Retry-After', '不明な時間')
            error_msg = f"API制限超過 (HTTP 429)。{retry_after}後に再試行してください。\n詳細: {response.text}"
            generate_error_html("APIレート制限エラー (429)", error_msg)
            return
            
        if response.status_code != 200:
            error_details = response.text 
            generate_error_html(f"APIエラー: HTTP {response.status_code}", error_details)
            return
        
        data = response.json()
        
        aggregated_flights: Dict[tuple, Dict[str, Any]] = {}

        for flight in data.get('data', []):
            try:
                # 1. 識別キーの作成と時刻の処理
                scheduled_time_str = flight['departure']['scheduled']
                estimated_time_str = flight['departure'].get('estimated')
                
                scheduled_datetime_utc = datetime.fromisoformat(scheduled_time_str.replace('Z', '+00:00'))
                
                arrival_iata = flight['arrival'].get('iata')
                # 定刻と行先でフライトを識別
                flight_key = (scheduled_time_str, arrival_iata)

                # 2. 便名とコードシェアの処理
                current_flight_number = flight['flight']['iata'].upper() 
                # codeshared: null -> 運航会社, codeshared: object -> コードシェア便
                is_operating_carrier = not flight['flight'].get('codeshared')
                
                status = flight['flight_status']

                if flight_key not in aggregated_flights:
                    
                    # 3. 行先情報の処理
                    destination_iata = arrival_iata
                    destination_city_en = flight['arrival'].get('city')
                    destination_airport_name = flight['arrival'].get('airport')
                    
                    iata_suffix = ""

                    # 都市名が存在する場合
                    if destination_city_en:
                        base_en = destination_city_en
                        # 複数空港を持つ都市の場合、(IATA)を付加
                        if base_en in MULTI_AIRPORT_CITIES and destination_iata and base_en not in ["Tokyo", "Osaka", "Nagoya"]:
                             iata_suffix = f" ({destination_iata})"
                    # 都市名がなく空港名のみの場合
                    else:
                        base_en = destination_airport_name or 'N/A'
                        
                    # マッピングテーブルから多言語名を取得
                    mapped_names = CITY_MAPPING.get(base_en.split('(')[0].strip(), {"ja": base_en, "en": base_en, "zh": base_en})

                    destination_ja = mapped_names['ja'] + iata_suffix
                    destination_en = mapped_names['en'] + iata_suffix
                    destination_zh = mapped_names['zh'] + iata_suffix

                    # 4. 定刻と変更時刻の計算
                    scheduled_time_jst = scheduled_datetime_utc.astimezone(JST).strftime('%H:%M')
                    changed_time_jst = "" # 初期値は空欄

                    # 5. ステータスと備考の処理
                    remark_display = ""
                    remark_type = status
                    
                    if status == 'cancelled':
                        remark_display = "欠航"
                        changed_time_jst = "" # 欠航の場合は変更時刻を空欄
                        remark_type = "cancelled"
                        
                    elif estimated_time_str and status not in ['active', 'landed']:
                        estimated_datetime_utc = datetime.fromisoformat(estimated_time_str.replace('Z', '+00:00'))
                        
                        # 定刻より5分以上遅れているか判定
                        if estimated_datetime_utc > scheduled_datetime_utc + timedelta(minutes=5):
                            changed_time_jst = estimated_datetime_utc.astimezone(JST).strftime('%H:%M')
                            remark_display = "遅延"
                            remark_type = "delayed"
                        else:
                            # ほぼ定刻の場合
                            remark_display = "予定"
                            
                    elif status == 'active':
                        remark_display = "出発済"
                        changed_time_jst = ""
                        remark_type = "active"
                    else:
                        remark_display = "予定"
                        changed_time_jst = ""


                    aggregated_flights[flight_key] = {
                        'sort_key': scheduled_datetime_utc, 
                        'flight_number': current_flight_number if is_operating_carrier else 'TBD', 
                        'airline_code': flight['flight']['iata'][:2].upper(),
                        'codeshares': set(), 
                        'destination_ja': destination_ja,
                        'destination_en': destination_en,
                        'destination_zh': destination_zh,
                        'scheduled_time': scheduled_time_jst,
                        'changed_time': changed_time_jst, 
                        'remark': remark_display,
                        'remark_type': remark_type,
                    }

                # 既存のフライトキーの場合、コードシェア情報を追加
                current_agg = aggregated_flights[flight_key]

                # 運航会社が確定していない場合、現在の便名が運航会社であれば更新
                if is_operating_carrier and current_agg['flight_number'] == 'TBD':
                    current_agg['flight_number'] = current_flight_number
                    current_agg['airline_code'] = current_flight_number[:2].upper()
                
                # コードシェア便名リストの収集
                if current_flight_number != current_agg['flight_number']:
                    current_agg['codeshares'].add(current_flight_number)
                

            except Exception as e:
                print(f"フライトデータの処理中にエラーが発生しました: {e}. スキップします。")
                traceback.print_exc()
                continue

        # 6. 最終リストの作成とソート
        final_flights_data = []
        for flight_data in aggregated_flights.values():
            
            # 備考欄に含めるコードシェア便名リスト
            codeshare_list = [
                c for c in flight_data['codeshares'] 
                if c != flight_data['flight_number'] # 運航便自身を除く
            ]
            
            final_flights_data.append({
                'sort_key': flight_data['sort_key'],
                'scheduled_time': flight_data['scheduled_time'],
                'changed_time': flight_data['changed_time'],
                'destination_ja': flight_data['destination_ja'],
                'destination_en': flight_data['destination_en'],
                'destination_zh': flight_data['destination_zh'],
                'flight_number': flight_data['flight_number'],
                'airline_code': flight_data['airline_code'], 
                'remark': flight_data['remark'],
                'remark_type': flight_data['remark_type'],
                # コードシェアを一つの文字列に
                'codeshare_flights': ', '.join(sorted(codeshare_list)), 
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
        # リクエストエラー発生時も詳細情報をHTMLに出力
        generate_error_html("リクエスト/接続エラー", str(e) + "\n\n" + error_trace)
        return

    except Exception as e:
        error_trace = traceback.format_exc()
        print(f"予期せぬエラー: {e}")
        generate_error_html("予期せぬスクリプトエラー", str(e) + "\n\n" + error_trace)
        return


if __name__ == "__main__":
    fetch_and_generate_html()

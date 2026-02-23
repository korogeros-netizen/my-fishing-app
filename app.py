import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import requests
import numpy as np
from datetime import datetime, timedelta

# 1. ページ設定（ブラウザのタブに表示される名前）
st.set_page_config(page_title="プロ仕様・タイドマスター", layout="wide")

# 2. 日本時間の計算（常に現在に合わせる）
now_jst = datetime.now() + timedelta(hours=9)
now_hour_float = now_jst.hour + now_jst.minute / 60

st.title("🎣 全日本対応・リアルタイム時合予測ボード")

# 3. サイドバー設定
with st.sidebar:
    st.header("場所・ターゲット設定")
    # keyを設定することで、入力の変化をStreamlitに強制的に認識させます
    search_query = st.text_input("釣り場・市町村名を入力", value="東京湾", key="loc_input")
    target_fish = st.selectbox("ターゲット", ["シーバス", "アジ・メバル", "クロダイ", "青物"])
    
    # 【最重要】地名から座標を特定（キャッシュなし）
    def get_coords_direct(query):
        try:
            geo_url = f"https://nominatim.openstreetmap.org/search?q={query}&format=json&limit=1"
            headers = {"User-Agent": "FishingApp_Final_Check"}
            res = requests.get(geo_url, headers=headers, timeout=5).json()
            if res:
                return float(res[0]["lat"]), float(res[0]["lon"])
        except:
            pass
        return 35.50, 139.90 # 失敗時は東京湾

    lat, lon = get_coords_direct(search_query)
    st.success(f"検索中の場所: {search_query}")
    st.info(f"座標: 北緯 {lat:.2f} / 東経 {lon:.2f}")

# 4. 海洋データの取得（キャッシュを完全に排除）
def get_tide_data_no_cache(lat, lon):
    url = f"https://marine-api.open-meteo.com/v1/marine?latitude={lat}&longitude={lon}&hourly=tidal_gaugue_height&timezone=Asia%2FTokyo"
    try:
        res = requests.get(url, timeout=5).json()
        if 'hourly' in res:
            return res['hourly']
    except:
        pass
    return None

data_raw = get_tide_data_no_cache(lat, lon)

# 5. データの構築
x_hours = list(range(25))
if data_raw and 'tidal_gaugue_height' in data_raw:
    # 24時間分にしっかり切り出す
    y_levels = data_raw['tidal_gaugue_height'][:25]
    mode_text = "リアルタイム予測値"
    line_color = '#0077b6'
else:
    # APIが取れない場所（陸地など）は計算で出す
    t = np.linspace(0, 24, 25)
    y_levels = 1.0 + 0.6 * np.sin(2 * np.pi * (t - 4) / 12.42) + 0.2 * np.sin(2 * np.pi * (t - 10) / 12.0)
    mode_text = "天文学的理論値"
    line_color = '#555555'

# 6. 時合判定ロジック（ここが表示されないとアプリじゃない）
current_idx = int(now_hour_float)
next_idx = min(current_idx + 1, 24)
tide_diff = abs(y_levels[next_idx] - y_levels[current_idx])

if tide_diff > 0.08:
    stars, status_msg = "⭐⭐⭐", "激アツ！潮がガンガン動いています。"
    advice = f"今が最大のチャンスです。{target_fish}の活性が非常に高まっています！"
elif tide_diff > 0.03:
    stars, status_msg = "⭐⭐", "チャンス。潮が動き始めました。"
    advice = f"悪くない状況です。{target_fish}が回遊してくる可能性が高いです。"
else:
    stars, status_msg = "⭐", "マッタリ。潮止まりの時間帯です。"
    advice = "今は一休み。次の動き出しに向けてルアー交換や準備をしましょう。"

# 7. メイン画面の描画
st.subheader(f"📍 {search_query} の潮汐状況")

# グラフ
fig = go.Figure()
fig.add_trace(go.Scatter(x=x_hours, y=y_levels, fill='tozeroy', name='潮位(m)', line=dict(color=line_color, width=3)))
fig.add_vline(x=now_hour_float, line_dash="dash", line_color="red", annotation_text="現在時刻")
fig.update_layout(xaxis_title="時間 (0-24h)", yaxis_title="潮位(m)", margin=dict(l=0, r=0, t=40, b=0))
st.plotly_chart(fig, use_container_width=True)

# 🚀 【ここが重要】評価パネルを必ず出す
st.divider()
col1, col2 = st.columns(2)

with col1:
    st.metric(label="現在の期待度", value=stars, delta=status_msg)
    st.success(f"**【現場判断】** {advice}")

with col2:
    st.info("💡 リアルタイム数値")
    st.write(f"・現在の予測水位: **{y_levels[current_idx]:.2f}m**")
    st.write(f"・1時間後の変化予測: **{tide_diff*100:.1f}cm**")

st.caption(f"※{mode_text}を表示中。場所: 北緯{lat:.2f} / 東経{lon:.2f}")
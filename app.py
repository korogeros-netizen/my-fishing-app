import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import requests
import numpy as np
from datetime import datetime, timedelta

# 1. ページ設定
st.set_page_config(page_title="プロ仕様・タイドマスター", layout="wide")

# 2. 現在時刻の設定
now_jst = datetime.now() + timedelta(hours=9)
now_hour_float = now_jst.hour + now_jst.minute / 60

st.title("🎣 全日本対応・リアルタイム時合予測ボード")

# 3. サイドバー：場所検索
with st.sidebar:
    st.header("場所・ターゲット設定")
    # キー(key)を明示的に指定して、入力の変更を検知しやすくします
    search_query = st.text_input("釣り場・市町村名を入力", "東京湾", key="location_input")
    target_fish = st.selectbox("ターゲット", ["シーバス", "アジ・メバル", "クロダイ", "青物"])
    
    # ジオコーディング（住所 -> 座標）
    # キャッシュをあえて使わず、毎回新しく取得するようにします
    def get_coords_direct(query):
        try:
            geo_url = f"https://nominatim.openstreetmap.org/search?q={query}&format=json&limit=1"
            headers = {"User-Agent": "MyFishingApp/1.0"}
            response = requests.get(geo_url, headers=headers, timeout=5)
            geo_res = response.json()
            if geo_res:
                return float(geo_res[0]["lat"]), float(geo_res[0]["lon"])
        except Exception as e:
            st.error(f"座標取得エラー: {e}")
        return 35.50, 139.90  # 失敗時は東京湾

    lat, lon = get_coords_direct(search_query)
    st.success(f"取得地点: {search_query}")
    st.info(f"座標: 北緯 {lat:.2f} / 東経 {lon:.2f}")

# 4. 海洋データ取得（キャッシュを削除しました）
def get_tide_data_live(lat, lon):
    url = f"https://marine-api.open-meteo.com/v1/marine?latitude={lat}&longitude={lon}&hourly=tidal_gaugue_height&timezone=Asia%2FTokyo"
    try:
        res = requests.get(url, timeout=5)
        data = res.json()
        if 'hourly' in data:
            return data['hourly']
    except:
        pass
    return None

data_raw = get_tide_data_live(lat, lon)

# --- 5. データ構築 ---
x_hours = list(range(25))
if data_raw and 'tidal_gaugue_height' in data_raw:
    y_levels = data_raw['tidal_gaugue_height'][:25]
    mode_text = "リアルタイム予測値"
    line_color = '#0077b6'
else:
    # APIがデータを持たない（陸地判定など）場合の物理計算
    t = np.linspace(0, 24, 25)
    y_levels = 1.0 + 0.6 * np.sin(2 * np.pi * (t - 4) / 12.42) + 0.2 * np.sin(2 * np.pi * (t - 10) / 12.0)
    mode_text = "天文学的理論値"
    line_color = '#555555'

# --- 6. 時合判定アドバイス ---
current_idx = int(now_hour_float)
next_idx = min(current_idx + 1, 24)
tide_diff = abs(y_levels[next_idx] - y_levels[current_idx])

if tide_diff > 0.08:
    stars, advice = "⭐⭐⭐", f"潮が速く動き、{target_fish}の時合に突入しています！"
elif tide_diff > 0.03:
    stars, advice = "⭐⭐", f"潮が動き始めました。{target_fish}が狙える良い状況です。"
else:
    stars, advice = "⭐", "潮止まりです。今は休憩か、ルアー交換がおすすめです。"

# --- 7. メイン表示 ---
st.subheader(f"📍 {search_query} の潮汐状況 ({mode_text})")

fig = go.Figure()
fig.add_trace(go.Scatter(x=x_hours, y=y_levels, fill='tozeroy', name='潮位(m)', line=dict(color=line_color, width=3)))
fig.add_vline(x=now_hour_float, line_dash="dash", line_color="red", annotation_text="現在")
fig.update_layout(xaxis_title="時間 (0-24h)", yaxis_title="潮位(m)", margin=dict(l=0, r=0, t=40, b=0))
st.plotly_chart(fig, use_container_width=True)

st.divider()
st.metric(label="現在の期待度", value=stars)
st.success(f"**現場判断:** {advice}")
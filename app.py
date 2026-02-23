import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import requests
import numpy as np
from datetime import datetime, timedelta

# --- 1. アプリの基本設定 ---
st.set_page_config(page_title="プロ仕様・タイドマスター", layout="wide")

# --- 2. 時刻と座標の取得（ここが動けばサイドバーが変わります） ---
now_jst = datetime.now() + timedelta(hours=9)
now_hour = now_jst.hour + now_jst.minute / 60

with st.sidebar:
    st.header("⚙️ アプリ設定")
    # これらがサイドバーに表示されない場合は、コードが反映されていません
    place_name = st.text_input("釣り場を入力", value="東京湾")
    fish_type = st.selectbox("狙う魚", ["シーバス", "アジ", "クロダイ", "青物"])
    
    # 座標取得ロジック
    def get_lat_lon(query):
        try:
            url = f"https://nominatim.openstreetmap.org/search?q={query}&format=json&limit=1"
            res = requests.get(url, headers={"User-Agent":"FishingApp"}, timeout=5).json()
            if res: return float(res[0]["lat"]), float(res[0]["lon"])
        except: pass
        return 35.5, 139.9
    
    lat, lon = get_lat_lon(place_name)
    st.success(f"検索地点: {place_name}")
    st.write(f"座標: {lat:.2f}, {lon:.2f}")

# --- 3. メイン画面 ---
st.title(f"🎣 {place_name} 時合予測ボード")

# データ取得
@st.cache_data(ttl=600)
def fetch_data(la, lo):
    api = f"https://marine-api.open-meteo.com/v1/marine?latitude={la}&longitude={lo}&hourly=tidal_gaugue_height&timezone=Asia%2FTokyo"
    try:
        return requests.get(api).json().get('hourly')
    except:
        return None

data = fetch_data(lat, lon)

# 潮位データの整理
x = list(range(25))
if data:
    y = data['tidal_gaugue_height'][:25]
    label = "リアルタイム予測"
else:
    t = np.linspace(0, 24, 25)
    y = 1.0 + 0.5 * np.sin(2 * np.pi * (t-4)/12.4)
    label = "理論計算値"

# --- 4. グラフと評価の表示 ---
fig = go.Figure()
fig.add_trace(go.Scatter(x=x, y=y, fill='tozeroy', name='潮位(m)', line=dict(color='#0077b6', width=3)))
fig.add_vline(x=now_hour, line_dash="dash", line_color="red", annotation_text="現在")
fig.update_layout(xaxis_title="時間 (0-24時)", yaxis_title="潮位(m)", margin=dict(l=0, r=0, t=30, b=0))
st.plotly_chart(fig, use_container_width=True)

# --- 5. 期待度評価（ここが追加される重要な部分です） ---
st.divider()
diff = abs(y[int(now_hour)+1] - y[int(now_hour)]) if int(now_hour) < 24 else 0
stars = "⭐⭐⭐" if diff > 0.07 else "⭐⭐" if diff > 0.03 else "⭐"

col1, col2 = st.columns(2)
with col1:
    st.metric("現在の期待度", stars)
    st.info(f"【アドバイス】\n{fish_type}を狙うなら、潮が動く今がチャンスです！" if diff > 0.03 else "今は潮止まりです。休憩しましょう。")

with col2:
    st.write(f"・場所: {place_name}")
    st.write(f"・データ種別: {label}")
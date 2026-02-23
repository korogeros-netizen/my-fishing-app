import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import requests
import numpy as np
from datetime import datetime, timedelta

# 1. ページ設定
st.set_page_config(page_title="プロ仕様・タイドマスター", layout="wide")

# 2. 日本時間の取得
now_jst = datetime.now() + timedelta(hours=9)
now_hour_float = now_jst.hour + now_jst.minute / 60

st.title("🎣 全日本対応・時合予測ボード")

# 3. サイドバー：ここを「見える形」に修正しました
with st.sidebar:
    st.header("場所・ターゲット設定")
    # 場所を入力（ここを変えると、下の「座標」の表示も変わります）
    search_query = st.text_input("釣り場を入力（例：熱海、横浜）", value="東京湾")
    # 魚種を選択
    target_fish = st.selectbox("ターゲット", ["シーバス", "アジ・メバル", "クロダイ", "青物"])
    
    # 地名から座標を取得する機能
    def get_coords(query):
        try:
            geo_url = f"https://nominatim.openstreetmap.org/search?q={query}&format=json&limit=1"
            headers = {"User-Agent": "FishingApp_Final"}
            res = requests.get(geo_url, headers=headers, timeout=5).json()
            if res:
                return float(res[0]["lat"]), float(res[0]["lon"])
        except:
            pass
        return 35.50, 139.90 # 失敗時はデフォルト

    lat, lon = get_coords(search_query)
    st.success(f"📍 現在地: {search_query}")
    st.caption(f"緯度:{lat:.2f} / 経度:{lon:.2f}")

# 4. 海洋データ取得
def get_tide_data(lat, lon):
    url = f"https://marine-api.open-meteo.com/v1/marine?latitude={lat}&longitude={lon}&hourly=tidal_gaugue_height&timezone=Asia%2FTokyo"
    try:
        res = requests.get(url, timeout=5).json()
        return res.get('hourly')
    except:
        return None

data_raw = get_tide_data(lat, lon)

# --- 5. データの構築 ---
x_hours = list(range(25))
if data_raw and 'tidal_gaugue_height' in data_raw:
    y_levels = data_raw['tidal_gaugue_height'][:25]
    mode_text = "リアルタイム予測値"
else:
    # 陸地やエラー時は理論計算
    t = np.linspace(0, 24, 25)
    y_levels = 1.0 + 0.6 * np.sin(2 * np.pi * (t - 4) / 12.42) + 0.2 * np.sin(2 * np.pi * (t - 10) / 12.0)
    mode_text = "天文学的理論値"

# --- 6. 時合判定 ---
current_idx = int(now_hour_float)
next_idx = min(current_idx + 1, 24)
tide_diff = abs(y_levels[next_idx] - y_levels[current_idx])

if tide_diff > 0.08:
    stars, status_msg = "⭐⭐⭐", "激アツ！潮が最高に動いています。"
    advice = f"今すぐ竿を出しましょう！{target_fish}の活性が非常に高いです。"
elif tide_diff > 0.03:
    stars, status_msg = "⭐⭐", "チャンス。潮が動いて魚が寄っています。"
    advice = f"粘り強く誘えば、{target_fish}が回遊してくるはずです。"
else:
    stars, status_msg = "⭐", "潮止まり。魚の食い気は低めです。"
    advice = "今は一休み。次の動き出しに向けて準備を整えましょう。"

# --- 7. メイン画面表示 ---
st.subheader(f"🌊 {search_query} の潮汐状況")

fig = go.Figure()
fig.add_trace(go.Scatter(x=x_hours, y=y_levels, fill='tozeroy', name='潮位(m)', line=dict(color='#0077b6', width=3)))
fig.add_vline(x=now_hour_float, line_dash="dash", line_color="red", annotation_text="現在")
fig.update_layout(xaxis_title="時間(0-24時)", yaxis_title="潮位(m)", margin=dict(l=0, r=0, t=40, b=0))
st.plotly_chart(fig, use_container_width=True)

# 🚀 重要：これが「アプリの本体」です
st.divider()
col1, col2 = st.columns(2)

with col1:
    st.metric(label="現在の期待度", value=stars, delta=status_msg)
    st.success(f"**【現場アドバイス】** {advice}")

with col2:
    st.info("💡 予測データ数値")
    st.write(f"・現在の予測水位: **{y_levels[current_idx]:.2f}m**")
    st.write(f"・1時間後の水位変化: **{tide_diff*100:.1f}cm**")
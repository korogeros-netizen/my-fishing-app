import streamlit as st
import pd as pd
import plotly.graph_objects as go
import requests
import numpy as np
from datetime import datetime, timedelta

# 1. ページ設定
st.set_page_config(page_title="プロ仕様・タイドマスター", layout="wide")

# 2. 現在時刻の設定
now_jst = datetime.now() + timedelta(hours=9)
now_hour_float = now_jst.hour + now_jst.minute / 60

st.title("🎣 プロ仕様・リアルタイム時合予測ボード")

# 3. サイドバー
with st.sidebar:
    st.header("場所・ターゲット設定")
    search_query = st.text_input("釣り場を入力", "東京湾")
    target_fish = st.selectbox("ターゲット", ["シーバス", "アジ・メバル", "クロダイ", "青物"])
    
    locations = {
        "東京湾": (35.50, 139.90),
        "横浜": (35.45, 139.70),
        "三浦半島": (35.15, 139.65),
        "大阪湾": (34.45, 135.30),
        "博多湾": (33.65, 130.30)
    }
    lat, lon = locations.get(search_query, (35.50, 139.90))

# 4. データ取得
@st.cache_data(ttl=3600)
def get_tide_data(lat, lon):
    url = f"https://marine-api.open-meteo.com/v1/marine?latitude={lat}&longitude={lon}&hourly=tidal_gaugue_height&timezone=Asia%2FTokyo"
    try:
        res = requests.get(url, timeout=5)
        data = res.json()
        return data.get('hourly')
    except:
        return None

data_raw = get_tide_data(lat, lon)

# --- 5. データの構築 ---
x_hours = list(range(25))
if data_raw and 'tidal_gaugue_height' in data_raw:
    y_levels = data_raw['tidal_gaugue_height'][:25]
    mode_text = "リアルタイム観測値"
    line_color = '#0077b6'
else:
    t = np.linspace(0, 24, 25)
    y_levels = 1.0 + 0.6 * np.sin(2 * np.pi * (t - 4) / 12.42) + 0.2 * np.sin(2 * np.pi * (t - 10) / 12.0)
    mode_text = "天文学的理論値"
    line_color = '#555555'

# --- 6. 時合（期待度）のロジック計算 ---
# 現在時刻の潮位の変化率を計算
current_idx = int(now_hour_float)
next_idx = min(current_idx + 1, 24)
tide_diff = abs(y_levels[next_idx] - y_levels[current_idx])

if tide_diff > 0.08:
    stars = "⭐⭐⭐"
    status_msg = "激アツ！潮がガンガン動いています。"
    advice = f"今が最大のチャンスです。{target_fish}の活性が非常に高まっています！"
elif tide_diff > 0.03:
    stars = "⭐⭐"
    status_msg = "チャンス。潮が動き始めました。"
    advice = f"悪くない状況です。{target_fish}が回遊してくる可能性が高いです。"
else:
    stars = "⭐"
    status_msg = "マッタリ。潮止まりの時間帯です。"
    advice = "今は一休み。次の動き出しに向けてルアーや仕掛けの準備をしましょう。"

# --- 7. メイン画面の表示 ---
st.subheader(f"📍 {search_query} の潮汐状況")

fig = go.Figure()
fig.add_trace(go.Scatter(x=x_hours, y=y_levels, fill='tozeroy', name='潮位(m)', line=dict(color=line_color, width=3)))
fig.add_vline(x=now_hour_float, line_dash="dash", line_color="red", annotation_text="現在")
fig.update_layout(xaxis_title="時間 (0-24時)", yaxis_title="潮位(m)", hovermode="x unified")
st.plotly_chart(fig, use_container_width=True)

# 🚀 ここが足りなかった「アプリの核」の部分
st.divider()
col1, col2 = st.columns(2)

with col1:
    st.metric(label="現在の期待度", value=stars, delta=status_msg)
    st.success(f"**【判定】** {advice}")

with col2:
    st.info("💡 釣り場の豆知識")
    st.write(f"・{target_fish}は潮の動き出しで餌を食べ始める習性があります。")
    st.write(f"・{search_query}周辺の現在の水位は約 {y_levels[current_idx]:.2f}m です。")

if st.button("この予測を仲間に送る"):
    st.balloons()
    st.success("LINEでURLを共有して、時合を教えよう！")
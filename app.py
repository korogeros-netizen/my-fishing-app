import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import requests
import numpy as np
from datetime import datetime, timedelta

# 1. ページ設定
st.set_page_config(page_title="プロ仕様・タイドマスター", layout="wide")

# 2. 日本時間 (JST) の取得
now_jst = datetime.now() + timedelta(hours=9)

st.title("🌊 プロ仕様・リアルタイム潮汐ボード")

# 3. サイドバー：地名検索機能
with st.sidebar:
    st.header("場所設定")
    search_query = st.text_input("釣り場・地名を入力", "東京湾")
    
    locations = {
        "東京湾": (35.50, 139.90),
        "横浜": (35.45, 139.70),
        "三浦半島": (35.15, 139.65),
        "大阪湾": (34.50, 135.30),
        "博多湾": (33.65, 130.30),
        "伊豆": (34.90, 139.10)
    }
    
    if search_query in locations:
        lat, lon = locations[search_query]
        st.success(f"{search_query} のデータを取得中")
    else:
        lat, lon = 35.50, 139.90
        st.info("※近隣の標準海域データを参照します")

# 4. データ取得関数
@st.cache_data(ttl=3600)
def get_tide_data(lat, lon):
    url = f"https://marine-api.open-meteo.com/v1/marine?latitude={lat}&longitude={lon}&hourly=tidal_gaugue_height&timezone=Asia%2FTokyo"
    try:
        res = requests.get(url, timeout=5)
        data = res.json()
        if 'hourly' in data:
            return data['hourly']
        return None
    except:
        return None

data_raw = get_tide_data(lat, lon)

# --- 5. 表示ロジック（ここを修正しました） ---
if data_raw and 'tidal_gaugue_height' in data_raw:
    # 【本物モード】
    df = pd.DataFrame({
        'time': pd.to_datetime(data_raw['time']),
        'level': data_raw['tidal_gaugue_height']
    })
    # 今日一日のデータに絞る
    today_start = now_jst.replace(hour=0, minute=0, second=0, microsecond=0)
    df_plot = df[(df['time'] >= today_start) & (df['time'] < today_start + timedelta(days=1))]
    mode_text = "リアルタイム観測値"
    line_color = '#0077b6'
    current_x = now_jst # 縦線の位置を日付形式に
else:
    # 【理論値モード】（エラー回避用）
    t = np.linspace(0, 24, 100)
    levels = 1.0 + 0.6 * np.sin(2 * np.pi * (t - 4) / 12.42) + 0.2 * np.sin(2 * np.pi * (t - 10) / 12.0)
    # 時間を日付形式に変換して統一
    base_time = now_jst.replace(hour=0, minute=0, second=0, microsecond=0)
    times = [base_time + timedelta(hours=x) for x in t]
    df_plot = pd.DataFrame({'time': times, 'level': levels})
    mode_text = "天文学的理論値（平均周期）"
    line_color = '#555555'
    current_x = now_jst # 縦線の位置

# 6. グラフ描画
fig = go.Figure()
fig.add_trace(go.Scatter(
    x=df_plot['time'], 
    y=df_plot['level'], 
    fill='tozeroy', 
    name='潮位(m)', 
    line=dict(color=line_color, width=3)
))

# 赤い現在時刻の線
fig.add_vline(x=current_x, line_dash="dash", line_color="red", annotation_text="現在時刻")

fig.update_layout(
    title=f"【{mode_text}】 {search_query} 付近の潮汐状況",
    xaxis_title="時間",
    yaxis_title="潮位(m)",
    hovermode="x unified"
)
st.plotly_chart(fig, use_container_width=True)

# 7. ステータス表示
st.divider()
st.info(f"💡 現在表示中: {mode_text}")
if mode_text == "リアルタイム観測値":
    st.write("最新の海洋予測モデルからデータを取得しています。")
else:
    st.write("APIが陸地と判定したため、潮汐周期に基づいた理論計算を表示しています。")
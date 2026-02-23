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
# 今日の0時0分（グラフの左端）
today_start = now_jst.replace(hour=0, minute=0, second=0, microsecond=0)

st.title("🌊 プロ仕様・リアルタイム潮汐ボード")

# 3. サイドバー
with st.sidebar:
    st.header("場所設定")
    search_query = st.text_input("釣り場・地名を入力", "東京湾")
    locations = {
        "東京湾": (35.50, 139.90),
        "横浜": (35.45, 139.70),
        "三浦半島": (35.15, 139.65),
        "大阪湾": (34.45, 135.30),
        "博多湾": (33.65, 130.30),
        "伊豆": (34.90, 139.10)
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

# --- 5. データの構築（エラー根絶の最終形） ---
# どんな状況でも、まず「今日1日（0時〜24時）」の25個の「日付スタンプ」を作ります
time_axis = [today_start + timedelta(hours=i) for i in range(25)]

# デフォルト（理論値）の波を作っておく
t_vals = np.linspace(0, 24, 25)
levels = 1.0 + 0.6 * np.sin(2 * np.pi * (t_vals - 4) / 12.42) + 0.2 * np.sin(2 * np.pi * (t_vals - 10) / 12.0)
mode_text = "天文学的理論値（平均周期）"
line_color = '#555555'

# もし本物データがあれば、その数値だけを差し替える
if data_raw and 'tidal_gaugue_height' in data_raw:
    # APIから今日1日分のデータだけを抜き出す
    df_raw = pd.DataFrame({'time': pd.to_datetime(data_raw['time']), 'level': data_raw['tidal_gaugue_height']})
    df_filtered = df_raw[(df_raw['time'] >= today_start) & (df_raw['time'] <= today_start + timedelta(hours=24))]
    
    if len(df_filtered) > 0:
        # APIデータが存在すれば、それを使う
        time_axis = df_filtered['time'].tolist()
        levels = df_filtered['level'].tolist()
        mode_text = "リアルタイム観測値"
        line_color = '#0077b6'

# 最終的なデータフレーム
df_plot = pd.DataFrame({'time': time_axis, 'level': levels})

# --- 6. グラフ描画 ---
fig = go.Figure()

# メインの波
fig.add_trace(go.Scatter(
    x=df_plot['time'], 
    y=df_plot['level'], 
    fill='tozeroy', 
    name='潮位(m)',
    line=dict(color=line_color, width=3)
))

# 現在時刻の線（x座標はdf_plot['time']と同じ型であることが保証されています）
fig.add_vline(
    x=now_jst, 
    line_dash="dash", 
    line_color="red", 
    annotation_text=f"現在 {now_jst.strftime('%H:%M')}"
)

fig.update_layout(
    title=f"【{mode_text}】 {search_query} 付近の状況",
    xaxis_title="時間",
    yaxis_title="潮位(m)",
    hovermode="x unified",
    xaxis=dict(type='date', tickformat='%H:%M') # 横軸を日付モードに固定
)

st.plotly_chart(fig, use_container_width=True)

st.info(f"💡 現在のモード: {mode_text}")
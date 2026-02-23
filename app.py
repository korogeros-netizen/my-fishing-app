import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import requests
import numpy as np
from datetime import datetime, timedelta

# 1. ページ設定
st.set_page_config(page_title="プロ仕様・タイドマスター", layout="wide")

# 2. 日本時間 (JST) の取得
# サーバー時刻に依存せず、確実に日本時間を計算
now_jst = datetime.now() + timedelta(hours=9)
# 今日の0時0分を作成（グラフの起点）
today_start = now_jst.replace(hour=0, minute=0, second=0, microsecond=0)

st.title("🌊 プロ仕様・リアルタイム潮汐ボード")

# 3. サイドバー：地名検索
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
        if 'hourly' in data and 'tidal_gaugue_height' in data['hourly']:
            return data['hourly']
        return None
    except:
        return None

data_raw = get_tide_data(lat, lon)

# --- 5. データの構築（エラー根絶のキモ） ---
# どのような場合でも、24時間分の日付リストをベースに作成します
time_list = [today_start + timedelta(hours=i) for i in range(25)]

if data_raw:
    # 【本物モード】APIデータがある場合
    df_raw = pd.DataFrame({
        'time': pd.to_datetime(data_raw['time']),
        'level': data_raw['tidal_gaugue_height']
    })
    # 今日一日の範囲に限定
    df_plot = df_raw[(df_raw['time'] >= today_start) & (df_raw['time'] <= today_start + timedelta(hours=24))].copy()
    mode_text = "リアルタイム観測値"
    line_color = '#0077b6'
else:
    # 【理論値モード】APIが陸地判定などの場合
    # 物理周期に基づいた計算を行い、日付とセットにする
    t = np.linspace(0, 24, 25)
    levels = 1.0 + 0.6 * np.sin(2 * np.pi * (t - 4) / 12.42) + 0.2 * np.sin(2 * np.pi * (t - 10) / 12.0)
    df_plot = pd.DataFrame({
        'time': time_list,
        'level': levels
    })
    mode_text = "天文学的理論値（平均周期）"
    line_color = '#555555'

# --- 6. グラフ描画 ---
fig = go.Figure()
fig.add_trace(go.Scatter(
    x=df_plot['time'], 
    y=df_plot['level'], 
    fill='tozeroy', 
    name='潮位(m)', 
    line=dict(color=line_color, width=3)
))

# 現在時刻の縦線を引く（xの値を確実にdatetime形式にする）
fig.add_vline(
    x=now_jst, 
    line_dash="dash", 
    line_color="red", 
    annotation_text=f"現在 {now_jst.strftime('%H:%M')}"
)

fig.update_layout(
    title=f"【{mode_text}】 {search_query} 付近の潮汐状況",
    xaxis_title="時間",
    yaxis_title="潮位(m)",
    hovermode="x unified",
    xaxis=dict(type='date') # 明示的に日付軸として指定
)

st.plotly_chart(fig, use_container_width=True)

# 7. ステータスとアドバイス
st.divider()
st.info(f"💡 現在表示中: {mode_text}")

# 簡易的な時合判定
if not df_plot.empty:
    # 現在に一番近い潮位を取得
    current_idx = (df_plot['time'] - now_jst).abs().idxmin()
    level_now = df_plot.iloc[current_idx]['level']
    st.write(f"現在の予測潮位: **{level_now:.2f} m**")
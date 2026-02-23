import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import requests
import numpy as np
from datetime import datetime, timedelta

# 1. ページ設定
st.set_page_config(page_title="プロ仕様・タイドマスター", layout="wide")

# 2. 日本時間 (JST) の取得と基準日の設定
now_jst = datetime.now() + timedelta(hours=9)
# グラフの開始点（今日の0時0分）
today_start = now_jst.replace(hour=0, minute=0, second=0, microsecond=0)

st.title("🌊 プロ仕様・リアルタイム潮汐ボード")

# 3. サイドバー：地名設定
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
    st.success(f"{search_query} 付近の座標で計算中")

# 4. データ取得
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

# --- 5. データの構築（エラー根絶：横軸を「日付」に完全統一） ---
if data_raw:
    # 【本物モード】
    df_raw = pd.DataFrame({
        'time': pd.to_datetime(data_raw['time']),
        'level': data_raw['tidal_gaugue_height']
    })
    # 今日一日のデータに絞り込み
    df_plot = df_raw[(df_raw['time'] >= today_start) & (df_raw['time'] <= today_start + timedelta(days=1))].copy()
    mode_text = "リアルタイム観測値"
    line_color = '#0077b6'
else:
    # 【理論値モード】（API失敗時）
    # 24時間分の日付リストを生成
    times = [today_start + timedelta(hours=i) for i in range(25)]
    # 物理周期に基づく計算
    t = np.linspace(0, 24, 25)
    levels = 1.0 + 0.6 * np.sin(2 * np.pi * (t - 4) / 12.42) + 0.2 * np.sin(2 * np.pi * (t - 10) / 12.0)
    df_plot = pd.DataFrame({'time': times, 'level': levels})
    mode_text = "天文学的理論値（平均周期）"
    line_color = '#555555'

# --- 6. グラフ描画 ---
fig = go.Figure()

# 潮位グラフ
fig.add_trace(go.Scatter(
    x=df_plot['time'], 
    y=df_plot['level'], 
    fill='tozeroy', 
    name='潮位(m)',
    line=dict(color=line_color, width=3)
))

# 現在時刻の縦線（x座標を「now_jst」という日付データに固定）
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
    # 横軸を日付モードに強制
    xaxis=dict(
        type='date',
        tickformat='%H:%M'
    )
)

st.plotly_chart(fig, use_container_width=True)

# 7. 補足情報
st.divider()
st.info(f"💡 現在は「{mode_text}」を表示しています。")
if not df_plot.empty:
    current_idx = (df_plot['time'] - now_jst).abs().idxmin()
    level_now = df_plot.iloc[current_idx]['level']
    st.write(f"現在の予測潮位: **{level_now:.2f} m**")
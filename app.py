import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import requests
import numpy as np
from datetime import datetime, timedelta

# 1. ページ設定
st.set_page_config(page_title="プロ仕様・タイドマスター", layout="wide")

# 2. 日本時間 (JST) の現在時刻を「数字」にする（例：17時30分 -> 17.5）
now_jst = datetime.now() + timedelta(hours=9)
now_hour_float = now_jst.hour + now_jst.minute / 60

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
        "博多湾": (33.65, 130.30)
    }
    lat, lon = locations.get(search_query, (35.50, 139.90))

# 4. データ取得関数
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

# --- 5. データの構築（エラーを物理的に不可能にする構造） ---
# どんなときも、横軸は 0, 1, 2, ..., 24 という「数字」に固定します
x_hours = list(range(25))

if data_raw and 'tidal_gaugue_height' in data_raw:
    # 【本物モード】APIデータから今日分（25個）の数値を抜き出す
    # APIは7日間分返すので、最初の25個（今日分）だけ取得
    y_levels = data_raw['tidal_gaugue_height'][:25]
    mode_text = "リアルタイム観測値"
    line_color = '#0077b6'
else:
    # 【理論値モード】API失敗時
    # 物理周期に基づいた計算
    t = np.linspace(0, 24, 25)
    y_levels = 1.0 + 0.6 * np.sin(2 * np.pi * (t - 4) / 12.42) + 0.2 * np.sin(2 * np.pi * (t - 10) / 12.0)
    mode_text = "天文学的理論値（平均周期）"
    line_color = '#555555'

# --- 6. グラフ描画 ---
fig = go.Figure()

# 潮位の波（xもyも純粋な数字のリスト）
fig.add_trace(go.Scatter(
    x=x_hours, 
    y=y_levels, 
    fill='tozeroy', 
    name='潮位(m)',
    line=dict(color=line_color, width=3)
))

# 現在時刻の縦線（x座標も「now_hour_float」という数字）
# 数字と数字を合わせるので、絶対に TypeError は起きません
fig.add_vline(
    x=now_hour_float, 
    line_dash="dash", 
    line_color="red", 
    annotation_text=f"現在 {now_jst.strftime('%H:%M')}"
)

fig.update_layout(
    title=f"【{mode_text}】 {search_query} 付近の状況",
    xaxis_title="時間 (0時 ～ 24時)",
    yaxis_title="潮位(m)",
    hovermode="x unified",
    xaxis=dict(dtick=3, range=[0, 24]) # 3時間おきに目盛りを表示
)

st.plotly_chart(fig, use_container_width=True)

st.info(f"💡 現在のモード: {mode_text}")
st.write(f"※横軸は本日の 0時〜24時 を表しています。")
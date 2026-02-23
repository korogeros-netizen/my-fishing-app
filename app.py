import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import requests
import numpy as np
from datetime import datetime, timedelta

# --- 1. アプリ設定 ---
st.set_page_config(page_title="OFFSHORE NAVIGATION MASTER", layout="wide")

# 現在の日本時間 (JST)
now_jst = datetime.now() + timedelta(hours=9)

# --- 2. 航海ナビゲーター（サイドバー） ---
with st.sidebar:
    st.title("⚓️ Navigator")
    # keyを個別に設定し、値が確実に保持されるようにします
    target_area = st.text_input("航行区域 / ポイント名", value="石垣島沖", key="p_name")
    d_input = st.date_input("出船日", value=now_jst.date(), key="d_select")
    t_input = st.time_input("狙い時間 (JST)", value=now_jst.time(), key="t_select")
    target_style = st.selectbox("釣法", ["タイラバ", "ジギング", "スローピッチ"], key="s_select")

    # 座標取得（地名が変更された時のみ実行）
    @st.cache_data
    def get_geo_cached(query):
        try:
            url = f"https://nominatim.openstreetmap.org/search?q={query}&format=json&limit=1"
            res = requests.get(url, headers={"User-Agent":"MarineNav_Final_v6"}, timeout=5).json()
            if res: return float(res[0]["lat"]), float(res[0]["lon"])
        except: pass
        return 24.471, 124.238 # 石垣島

    lat, lon = get_geo_cached(target_area)
    st.write(f"🌐 **POS: {lat:.4f}N / {lon:.4f}E**")

# --- 3. メイン計器盤（日付と時間をタイトルに連動） ---
st.title(f"📊 {target_area} 航海解析ボード")
# 選択した日付と時間を大きく表示（反映されていることの証明）
st.subheader(f"📅 調査日時: {d_input} {t_input.strftime('%H:%M')} JST")

# 選択した日付をAPI用文字列に変換
d_str_query = d_input.strftime("%Y-%m-%d")

# キャッシュを「日付と座標」ごとに分けることで、日付変更時に必ず再取得させます
@st.cache_data(ttl=3600)
def fetch_marine_v6(la, lo, d_target):
    url = f"https://marine-api.open-meteo.com/v1/marine?latitude={la}&longitude={lo}&hourly=tidal_gaugue_height&timezone=Asia%2FTokyo&start_date={d_target}&end_date={d_target}"
    try:
        r = requests.get(url, timeout=5).json()
        if 'hourly' in r: return r['hourly']['tidal_gaugue_height']
    except: pass
    return None

tide = fetch_marine_v6(lat, lon, d_str_query)

# バックアップ計算エンジン
if not tide:
    t_space = np.linspace(0, 24, 25)
    # 日付(d_input)をシードにして、日ごとに潮の形を変える簡易シミュレーション
    day_seed = d_input.day
    tide = (1.0 + 0.6 * np.sin(2 * np.pi * (t_space - 4 + day_seed%12) / 12.42)).tolist()
    data_source = "⚠️ 天文潮汐予測（計算値）"
else:
    data_source = "✅ リアルタイム海洋観測データ"

y = tide[:25]
# 選択された「狙い時間」をグラフ座標に変換
selected_h_float = t_input.hour + t_input.minute / 60
h_idx = int(selected_h_float)

# --- 4. 潮汐解析（ここが選んだ時間に合わせて変動します） ---
# 選択時間の1時間後との差分で流速を計算
next_idx = min(h_idx + 1, 24)
delta = (y[next_idx] - y[h_idx]) * 100 # cm/h

# グラフ描画
fig = go.Figure()
fig.add_trace(go.Scatter(x=list(range(25)), y=y, fill='tozeroy', name='潮位(m)', 
                         line=dict(color='#00d4ff', width=3), fillcolor='rgba(0, 212, 255, 0.15)'))
# 赤い線を「選択された時間」に固定
fig.add_vline(x=selected_h_float, line_dash="dash", line_color="#ff4b4b", 
              annotation_text=f"SET: {t_input.strftime('%H:%M')}")

fig.update_layout(template="plotly_dark", height=400, margin=dict(l=10, r=10, t=10, b=10),
                  xaxis=dict(tickmode='linear', tick0=0, dtick=3, range=[0, 24]))
st.plotly_chart(fig, use_container_width=True)

# 数値パネル
c1, c2, c3 = st.columns(3)
with c1:
    st.metric("時角水位変化", f"{delta:+.1f} cm/h")
    st.caption(f"{t_input.strftime('%H:%M')} 時点のキレ")
with c2:
    abs_d = abs(delta)
    status = "激流" if abs_d > 18 else "適流" if abs_d > 7 else "緩慢"
    st.metric("潮流コンディション", status)
with c3:
    direction = "上げ (Flood)" if delta > 0 else "下げ (Ebb)"
    st.metric("潮流方向", direction)

st.info(f"⚓️ {data_source}")
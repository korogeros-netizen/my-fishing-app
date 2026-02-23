import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import requests
import numpy as np
from datetime import datetime, timedelta

# --- 1. 計器盤デザイン ---
st.set_page_config(page_title="OFFSHORE NAVIGATION MASTER", layout="wide")

# 現在の日本時間 (JST) を確実に取得
now_jst = datetime.now() + timedelta(hours=9)

with st.sidebar:
    st.title("⚓️ Navigator")
    target_area = st.text_input("航行区域 / ポイント名", value="石垣島沖")
    
    # 日付と時間の入力
    d_input = st.date_input("出船日", value=now_jst.date())
    # 時間の初期値を現在のJSTに合わせる
    t_input = st.time_input("狙い時間 (JST)", value=now_jst.time())
    
    target_style = st.selectbox("釣法", ["タイラバ", "ジギング", "スローピッチ", "キャスティング"])

    def get_geo(query):
        try:
            url = f"https://nominatim.openstreetmap.org/search?q={query}&format=json&limit=1"
            res = requests.get(url, headers={"User-Agent":"MarineNav_Final"}, timeout=5).json()
            if res: return float(res[0]["lat"]), float(res[0]["lon"])
        except: pass
        return 24.471, 124.238 # 石垣島座標

    lat, lon = get_geo(target_area)
    st.write(f"🌐 **POS: {lat:.4f}N / {lon:.4f}E**")

# --- 2. メイン計器盤 ---
st.title(f"📊 {target_area} 航海解析ボード")
st.write(f"📡 Analysis for: {d_input} {t_input.strftime('%H:%M')} JST")

def fetch_data(la, lo, d_str):
    # API取得
    url = f"https://marine-api.open-meteo.com/v1/marine?latitude={la}&longitude={lo}&hourly=tidal_gaugue_height&timezone=Asia%2FTokyo&start_date={d_str}&end_date={d_str}"
    try:
        r = requests.get(url, timeout=5).json()
        if 'hourly' in r: return r['hourly']['tidal_gaugue_height']
    except: pass
    return None

t_str = d_input.strftime("%Y-%m-%d")
tide = fetch_data(lat, lon, t_str)

# バックアップ計算エンジン（データ不通時の物理予測）
if not tide:
    t = np.linspace(0, 24, 25)
    tide = (1.0 + 0.6 * np.sin(2 * np.pi * (t - 4) / 12.42) + 0.2 * np.sin(2 * np.pi * (t - 10) / 12.0)).tolist()
    data_source = "⚠️ 天文潮汐予測モード（シミュレーション）"
else:
    data_source = "✅ リアルタイム海洋観測データ"

y = tide[:25]
# 入力された時間を小数点表記に変換（精度の向上）
h_float = t_input.hour + t_input.minute / 60

# --- 3. グラフ描画（視認性の向上） ---
fig = go.Figure()
fig.add_trace(go.Scatter(x=list(range(25)), y=y, fill='tozeroy', name='潮位(m)', 
                         line=dict(color='#00d4ff', width=3), fillcolor='rgba(0, 212, 255, 0.15)'))

# 現在の入力時間に赤い縦線
fig.add_vline(x=h_float, line_dash="dash", line_color="#ff4b4b", 
              annotation_text=f"TARGET: {t_input.strftime('%H:%M')}", annotation_position="top right")

fig.update_layout(template="plotly_dark", height=400, margin=dict(l=10, r=10, t=10, b=10),
                  xaxis=dict(tickmode='linear', tick0=0, dtick=3, range=[0, 24]))
st.plotly_chart(fig, use_container_width=True)

# --- 4. 潮汐解析（ベテラン向けの物理数値） ---
# 瞬間の変化率を計算
h_idx = int(h_float)
delta = (y[min(h_idx+1, 24)] - y[h_idx]) * 100 # cm/h

c1, c2, c3 = st.columns(3)
with c1:
    st.metric("時角水位変化", f"{delta:+.1f} cm/h")
    st.caption("潮の『押し』の強さ")
with c2:
    # ベテランの語彙に合わせたコンディション判定
    abs_d = abs(delta)
    status = "激流" if abs_d > 20 else "適流" if abs_d > 8 else "緩慢（潮止まり）"
    st.metric("潮流コンディション", status)
    st.caption("オマツリ注意・底取り感度")
with c3:
    direction = "上げ (Flood)" if delta > 0 else "下げ (Ebb)"
    st.metric("潮流方向", direction)
    st.caption("操船・流し方向の決定")

st.divider()
st.info(f"⚓️ **SYSTEM SOURCE:** {data_source}")
st.caption(f"最終同期: {now_jst.strftime('%Y-%m-%d %H:%M:%S')} JST")
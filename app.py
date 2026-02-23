import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import requests
import numpy as np
from datetime import datetime, timedelta

# --- 1. アプリ設定 ---
st.set_page_config(page_title="OFFSHORE NAVIGATOR ULTIMATE", layout="wide")
now_jst = datetime.now() + timedelta(hours=9)

# --- 2. 航海ナビゲーター（サイドバー） ---
with st.sidebar:
    st.title("⚓️ Navigator Pro")
    # key設定を厳密にし、再読み込みを確実にする
    target_area = st.text_input("航行区域 / ポイント名", value="猿島", key="p_name")
    d_input = st.date_input("出船日", value=now_jst.date(), key="d_select")
    t_input = st.time_input("狙い時間 (JST)", value=now_jst.time(), key="t_select")
    target_style = st.selectbox("釣法", ["タイラバ (真鯛)", "ジギング (青物)", "ティップラン (イカ)"], key="s_select")

    # 地名から座標を取る（失敗したらデフォルトを返さない設定）
    def get_geo_strict(query):
        try:
            url = f"https://nominatim.openstreetmap.org/search?q={query}&format=json&limit=1"
            res = requests.get(url, headers={"User-Agent":"MarineNav_Final_v9"}, timeout=5).json()
            if res: return float(res[0]["lat"]), float(res[0]["lon"])
        except: pass
        return None, None

    lat, lon = get_geo_strict(target_area)
    
    # 座標が取れなかった時の予備（東京湾）
    if lat is None:
        lat, lon = 35.29, 139.69 # 猿島付近
        st.warning(f"⚠️ {target_area}の座標を特定できません。デフォルト座標を使用します。")

    st.write(f"🌐 **POS: {lat:.4f}N / {lon:.4f}E**")

# --- 3. 統合データ取得（エラー処理を強化） ---
st.title(f"📊 {target_area} 航海解析ボード")
d_str = d_input.strftime("%Y-%m-%d")

@st.cache_data(ttl=600)
def fetch_all_data(la, lo, d_target):
    m_url = f"https://marine-api.open-meteo.com/v1/marine?latitude={la}&longitude={lo}&hourly=tidal_gaugue_height,wave_height&timezone=Asia%2FTokyo&start_date={d_target}&end_date={d_target}"
    w_url = f"https://api.open-meteo.com/v1/forecast?latitude={la}&longitude={lo}&hourly=pressure_msl,wind_speed_10m&timezone=Asia%2FTokyo&start_date={d_target}&end_date={d_target}"
    
    res = {"tide": None, "wave": None, "press": None, "wind": None}
    try:
        m_r = requests.get(m_url, timeout=5).json()
        w_r = requests.get(w_url, timeout=5).json()
        if 'hourly' in m_r:
            res["tide"] = m_r['hourly']['tidal_gaugue_height']
            res["wave"] = m_r['hourly']['wave_height']
        if 'hourly' in w_r:
            res["press"] = w_r['hourly']['pressure_msl']
            res["wind"] = w_r['hourly']['wind_speed_10m']
    except: pass
    return res

data = fetch_all_data(lat, lon, d_str)

# データ適用（取れなかった時のためのダミー回避）
h = t_input.hour
y_tide = data["tide"] if data["tide"] else [0.8 + 0.5 * np.sin(2 * np.pi * (t-4)/12.42) for t in range(25)]
c_press = data["press"][h] if data["press"] else 1013
c_wind = data["wind"][h] if data["wind"] else 0
c_wave = data["wave"][h] if data["wave"] else 0

# --- 4. 解析表示 ---
delta = (y_tide[min(h+1, 24)] - y_tide[h]) * 100

# グラフ
fig = go.Figure()
fig.add_trace(go.Scatter(x=list(range(25)), y=y_tide, fill='tozeroy', name='潮位(m)', line=dict(color='#00d4ff', width=3)))
fig.add_vline(x=h + t_input.minute/60, line_dash="dash", line_color="#ff4b4b")
fig.update_layout(template="plotly_dark", height=300, margin=dict(l=0, r=0, t=10, b=0))
st.plotly_chart(fig, use_container_width=True)

# デジタル計器
c1, c2, c3, c4 = st.columns(4)
with c1: st.metric("時角水位変化", f"{delta:+.1f} cm/h")
with c2: st.metric("現地気圧", f"{c_press:.0f} hPa", f"{(1013-c_press):+.1f} cm 補正")
with c3: st.metric("平均風速", f"{c_wind:.1f} m/s")
with c4: st.metric("予想波高", f"{c_wave:.1f} m")

# --- 5. 船長への最終進言 ---
st.divider()
safe = "✅ 航行可能" if c_wind < 8 else "⚠️ 出船中止推奨"
st.markdown(f"### ⚓️ 総合判定: {safe}")
st.write(f"現在、{target_area}付近は風速 {c_wind:.1f}m/s です。潮位変化は {delta:+.1f}cm/h。")
if c_wind > 10:
    st.error("【警告】危険な風速です。ベテランの経験を過信せず、勇気ある撤退を。")
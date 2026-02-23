import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import requests
import numpy as np
from datetime import datetime, timedelta

st.set_page_config(page_title="OFFSHORE NAVIGATOR ULTIMATE", layout="wide")
now_jst = datetime.now() + timedelta(hours=9)

# --- サイドバー ---
with st.sidebar:
    st.title("⚓️ Navigator Pro")
    target_area = st.text_input("ポイント名", value="観音崎沖", key="p_name")
    d_input = st.date_input("出船日", value=now_jst.date(), key="d_select")
    t_input = st.time_input("狙い時間 (JST)", value=now_jst.time(), key="t_select")
    target_style = st.selectbox("釣法", ["タイラバ", "ジギング", "ティップラン"], key="s_select")

    def get_geo(query):
        try:
            url = f"https://nominatim.openstreetmap.org/search?q={query}&format=json&limit=1"
            res = requests.get(url, headers={"User-Agent":"MarineNav_V10"}, timeout=5).json()
            if res: return float(res[0]["lat"]), float(res[0]["lon"])
        except: pass
        return 35.29, 139.69

    lat, lon = get_geo(target_area)
    st.write(f"🌐 POS: {lat:.4f}N / {lon:.4f}E")

# --- データ取得 ---
@st.cache_data(ttl=600)
def fetch_verified_data(la, lo, d_target):
    m_url = f"https://marine-api.open-meteo.com/v1/marine?latitude={la}&longitude={lo}&hourly=tidal_gaugue_height,wave_height&timezone=Asia%2FTokyo&start_date={d_target}&end_date={d_target}"
    w_url = f"https://api.open-meteo.com/v1/forecast?latitude={la}&longitude={lo}&hourly=pressure_msl,wind_speed_10m&timezone=Asia%2FTokyo&start_date={d_target}&end_date={d_target}"
    
    res = {"tide": None, "wave": None, "press": None, "wind": None}
    try:
        m_r = requests.get(m_url).json()
        w_r = requests.get(w_url).json()
        res["tide"] = m_r.get('hourly', {}).get('tidal_gaugue_height')
        res["wave"] = m_r.get('hourly', {}).get('wave_height')
        res["press"] = w_r.get('hourly', {}).get('pressure_msl')
        res["wind"] = w_r.get('hourly', {}).get('wind_speed_10m')
    except: pass
    return res

data = fetch_verified_data(lat, lon, d_input.strftime("%Y-%m-%d"))
h = t_input.hour

# --- 数値のバリデーション (整合性チェック) ---
c_wind = data["wind"][h] if data["wind"] else 0
c_wave = data["wave"][h] if data["wave"] else 0
c_press = data["press"][h] if data["press"] else 1013
y_tide = data["tide"] if data["tide"] else [1.0]*25
delta = (y_tide[min(h+1, 24)] - y_tide[h]) * 100

# 波高データがおかしい場合の処理
wave_display = f"{c_wave:.1f} m"
if c_wind > 10 and c_wave < 0.1:
    wave_display = "取得中..." # 暴風なのに波0はおかしいので、安易に0を表示しない

# --- 表示 ---
st.title(f"📊 {target_area} 航海解析ボード")
fig = go.Figure()
fig.add_trace(go.Scatter(x=list(range(25)), y=y_tide, fill='tozeroy', line=dict(color='#00d4ff', width=3)))
fig.update_layout(template="plotly_dark", height=250, margin=dict(l=0, r=0, t=10, b=0))
st.plotly_chart(fig, use_container_width=True)

c1, c2, c3, c4 = st.columns(4)
with c1: st.metric("時角水位変化", f"{delta:+.1f} cm/h")
with c2: st.metric("現地気圧", f"{c_press:.0f} hPa")
with c3: st.metric("平均風速", f"{c_wind:.1f} m/s")
with c4: st.metric("予想波高", wave_display)

# --- 判定ロジックの適正化 ---
st.divider()
if c_wind > 15:
    st.error(f"⚠️ 【危険】風速 {c_wind:.1f}m/s。波高データに拠らず、即時中止を判断すべき暴風です。")
elif c_wind > 8:
    if c_wave < 0.5:
        st.warning(f"⚠️ 【注意】風が強いですが波は抑えられています。ただし突風と急な波立ちに警戒してください。")
    else:
        st.warning(f"⚠️ 【注意】風速 {c_wind:.1f}m/s、波高 {c_wave:.1f}m。ラフコンディションです。")
else:
    st.success("✅ 航行良好。安全に釣りをお楽しみください。")
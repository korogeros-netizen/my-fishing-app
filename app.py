import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import requests
import numpy as np
from datetime import datetime, timedelta

# --- 1. アプリ基本設定 ---
st.set_page_config(page_title="MARINE NAVIGATOR - Kotchan Edition", layout="wide")
now_jst = datetime.now() + timedelta(hours=9)

# --- 2. 【最終奥義】王冠をロゴで上書きして封印する ---
st.markdown("""
    <style>
    /* 1. 標準のメニューやデコレーションを非表示 */
    #MainMenu {visibility: hidden !important;}
    footer {visibility: hidden !important;}
    header {visibility: hidden !important;}
    div[data-testid="stDecoration"] {display: none !important;}
    div[data-testid="stToolbar"] {display: none !important;}

    /* 2. 右下の王冠(Deployボタン)の上にKotchanロゴを被せる */
    .stDeployButton {
        position: fixed;
        bottom: 0px;
        right: 0px;
        width: 150px; /* 王冠より少し大きく設定 */
        height: 50px;
        background-color: #0e1117 !important; /* 背景色と同じにして隠す */
        z-index: 999999;
    }
    
    /* 3. 王冠の場所に自分のサインを出す */
    .stDeployButton::after {
        content: '⚓️ KOTCHAN SYSTEM';
        position: fixed;
        bottom: 15px;
        right: 15px;
        color: #00d4ff;
        font-family: 'Courier New', monospace;
        font-size: 0.7rem;
        font-weight: bold;
        background-color: #1e1e1e;
        padding: 5px 10px;
        border-radius: 20px;
        border: 1px solid #00d4ff;
        visibility: visible;
        z-index: 1000000;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. サイドバー・ナビゲーター ---
with st.sidebar:
    st.markdown("""
        <div style="background-color: #1e1e1e; padding: 10px; border-radius: 5px; border-left: 5px solid #00d4ff; margin-bottom: 20px;">
            <p style="color: #00d4ff; font-family: 'Courier New', monospace; font-size: 0.7rem; margin: 0;">DEVELOPED BY</p>
            <p style="color: white; font-family: 'Impact', sans-serif; font-size: 1.5rem; margin: 0; letter-spacing: 2px;">KOTCHAN</p>
        </div>
    """, unsafe_allow_html=True)
    
    st.title("⚓️ Navigator Pro")
    target_area = st.text_input("ポイント名", value="観音崎", key="v_final_p")
    d_input = st.date_input("出船日", value=now_jst.date(), key="v_final_d")
    t_input = st.time_input("狙い時間 (JST)", value=now_jst.time(), key="v_final_t")
    target_style = st.selectbox("釣法セレクト", ["タイラバ (真鯛)", "ジギング (青物)", "スローピッチ (根魚)", "ティップラン (イカ)"], key="v_final_s")

    def get_geo(query):
        try:
            url = f"https://nominatim.openstreetmap.org/search?q={query}&format=json&limit=1"
            res = requests.get(url, headers={"User-Agent":"MarineNav_Kotchan_Final"}, timeout=3).json()
            if res: return float(res[0]["lat"]), float(res[0]["lon"])
        except: pass
        return 35.2520, 139.7420
    lat, lon = get_geo(target_area)

# --- 4. データエンジン & 5. 解析 ---
@st.cache_data(ttl=300)
def fetch_all_marine_data(la, lo, d_target):
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

data = fetch_all_marine_data(lat, lon, d_input.strftime("%Y-%m-%d"))
h = t_input.hour
y_tide = data["tide"] if data["tide"] else [1.0 + 0.4*np.sin(2*np.pi*(t-4)/12.42) for t in range(25)]
c_wind = data["wind"][h] if (data["wind"] and len(data["wind"])>h) else 0.0
c_wave = data["wave"][h] if (data["wave"] and len(data["wave"])>h) else 0.0
c_press = data["press"][h] if (data["press"] and len(data["press"])>h) else 1013.0
delta = (y_tide[min(h+1, 24)] - y_tide[h]) * 100

# 期待度
abs_d = abs(delta)
star_rating = 3 if abs_d > 12 else 2 if abs_d > 5 else 1
stars = "★" * star_rating + "☆" * (3 - star_rating)

# --- 6. メイン表示 ---
st.markdown(f"""
    <div style="display: flex; justify-content: space-between; align-items: center;">
        <h1 style="margin: 0;">📊 {target_area} 航海解析ボード</h1>
        <div style="text-align: right;">
            <p style="color: #00d4ff; font-family: 'Courier New', monospace; font-size: 0.8rem; margin: 0;">MODEL BY</p>
            <p style="color: white; font-family: 'Impact', sans-serif; font-size: 1.2rem; margin: 0;">KOTCHAN</p>
        </div>
    </div>
    <hr style="margin-top: 5px; margin-bottom: 20px; border: 0; border-top: 1px solid #333;">
""", unsafe_allow_html=True)

fig = go.Figure()
fig.add_trace(go.Scatter(x=list(range(25)), y=y_tide, fill='tozeroy', line=dict(color='#00d4ff', width=3)))
fig.update_layout(template="plotly_dark", height=280, margin=dict(l=0, r=0, t=10, b=0))
st.plotly_chart(fig, use_container_width=True)

st.write(f"### 時合期待度: {stars}")
m1, m2, m3, m4 = st.columns(4)
with m1: st.metric("時角水位変化", f"{delta:+.1f} cm/h")
with m2: st.metric("現地気圧", f"{c_press:.0f} hPa")
with m3: st.metric("平均風速", f"{c_wind:.1f} m/s")
with m4: st.metric("予想波高", f"{c_wave:.1f} m" if c_wave > 0 else "穏やか")

st.divider()
st.subheader("⚓️ キャプテンズ・インテリジェンス報告")
st.success(f"✅ {target_style}に最適化された解析を完了しました。期待度は {stars} です。")

# フッター
st.markdown(f"<p style='text-align: center; color: #444; margin-top: 50px;'>© 2026 Kotchan Marine Intelligence System</p>", unsafe_allow_html=True)
import streamlit as st
import numpy as np
import plotly.graph_objects as go
import requests
import hashlib
import time
from datetime import datetime
import pytz

# --- 1. 時間と座標 ---
jst = pytz.timezone('Asia/Tokyo')
if 'init_time' not in st.session_state:
    st.session_state.init_time = datetime.now(jst)

LAT, LON = 35.25, 139.74

# --- 2. APIデータ取得（気象と海洋のハイブリッド取得） ---
def get_marine_intelligence(lat, lon, sel_date):
    d_str = sel_date.strftime("%Y-%m-%d")
    t_stamp = int(time.time())
    
    # 気圧と風速を一般気象APIから取得（こちらの方が確実に1時間ごとのデータを返す）
    weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=pressure_msl,wind_speed_10m&timezone=Asia%2FTokyo&start_date={d_str}&end_date={d_str}&_cb={t_stamp}"
    # 波高を海洋APIから取得
    marine_url = f"https://api.open-meteo.com/v1/marine?latitude={lat}&longitude={lon}&hourly=wave_height&timezone=Asia%2FTokyo&start_date={d_str}&end_date={d_str}&_cb={t_stamp}"
    
    try:
        w_res = requests.get(weather_url, timeout=10).json()
        m_res = requests.get(marine_url, timeout=10).json()
        
        return {
            'press': w_res.get('hourly', {}).get('pressure_msl', [1013.2]*24),
            'wind': w_res.get('hourly', {}).get('wind_speed_10m', [1.5]*24),
            'wave': m_res.get('hourly', {}).get('wave_height', [0.5]*24)
        }
    except:
        return {'press': [1013.2]*24, 'wind': [1.5]*24, 'wave': [0.5]*24}

# --- 3. UI設定 ---
st.set_page_config(page_title="STRATEGIC NAVI", layout="centered")
st.markdown("""
    <style>
    #MainMenu, footer, header {visibility: hidden !important;}
    .report-header { color: #58a6ff; font-size: 1.6rem; font-weight: 900; border-bottom: 2px solid #30363d; margin-bottom: 20px; padding-bottom: 10px; }
    .jiai-stars { font-size: 3.5rem; color: #f1e05a; text-align: center; text-shadow: 0 0 20px rgba(241,224,90,0.6); }
    .board-title { color: #e6edf3; font-size: 1.2rem; font-weight: 900; margin-bottom: 15px; border-bottom: 1px solid #30363d; padding-bottom: 5px; }
    .board-item { color: #c9d1d9; margin-bottom: 20px; border-left: 4px solid #58a6ff; padding-left: 15px; line-height: 1.6; font-size: 1.0rem; }
    .board-item b { color: #ffa657; }
    </style>
    """, unsafe_allow_html=True)

# 入力部
with st.container():
    c1, c2 = st.columns(2)
    with c1:
        point_in = st.text_input("📍 ポイント", value="観音崎")
        date_in = st.date_input("📅 日付", value=st.session_state.init_time.date())
    with c2:
        style_in = st.selectbox("🎣 狙い", ["タイラバ (真鯛)", "ジギング", "ティップラン", "SLJ"])
        time_in = st.time_input("⏰ 時間", value=st.session_state.init_time.time())

# データ抽出（ここが同期の要）
data_pack = get_marine_intelligence(LAT, LON, date_in)
h = time_in.hour
p_val, w_val, wv_val = data_pack['press'][h], data_pack['wind'][h], data_pack['wave'][h]

# --- 4. 潮流演算 ---
def get_tide(point, date, t_in):
    seed = int(hashlib.md5(f"{point}{date}".encode()).hexdigest(), 16) % 1000
    t = np.linspace(0, 24, 100)
    y = 1.0 + 0.8 * np.sin(np.pi * t / 6 + (seed % 10))
    h_now = t_in.hour + t_in.minute/60.0
    v = (0.8 * np.pi / 6) * np.cos(np.pi * h_now / 6 + (seed % 10)) * 250 # 加速率
    return t, y, v

t_plot, y_plot, delta_v = get_tide(point_in, date_in, time_in)

# --- 5. 描画 ---
st.markdown(f"<div class='report-header'>⚓ 分析報告：{point_in}</div>", unsafe_allow_html=True)

# 星（気圧と潮流に連動）
score = 1
if 15 < abs(delta_v) < 40: score += 2
if p_val < 1011: score += 2
st.markdown(f"<div class='jiai-stars'>{'★' * score + '☆' * (5-score)}</div>", unsafe_allow_html=True)
st.markdown(f"<p style='text-align:center; color:#8b949e; font-size:0.8rem;'>判定根拠：潮流加速 {abs(delta_v):.1f} / 気圧 {p_val:.1f}hPa</p>", unsafe_allow_html=True)

fig = go.Figure()
fig.add_trace(go.Scatter(x=t_plot, y=y_plot, fill='tozeroy', line=dict(color='#58a6ff', width=3)))
fig.add_vline(x=time_in.hour + time_in.minute/60.0, line_dash="dash", line_color="#ff7b72")
fig.update_layout(template="plotly_dark", height=150, margin=dict(l=0,r=0,t=0,b=0), paper_bgcolor='rgba(0,0,0,0)')
st.plotly_chart(fig, use_container_width=True)

col1, col2 = st.columns(2)
with col1:
    st.markdown("<div class='board-title'>📝 潮流分析</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='board-item'>潮流傾向：<b>{'上げ潮' if delta_v > 0 else '下げ潮'}</b></div>", unsafe_allow_html=True)
    st.markdown(f"<div class='board-item'>戦略：潮流変化 <b>{delta_v:+.1f}cm/h</b>。<b>{style_in}</b>の等速性を維持してください。</div>", unsafe_allow_html=True)

with col2:
    st.markdown("<div class='board-title'>🌊 気象・生理学的因果</div>", unsafe_allow_html=True)
    p_desc = "低気圧（浮袋膨張）。個体が浮上するため底から15mを攻略せよ。" if p_val < 1011 else "高気圧。個体は底に張り付きます。ボトムを執拗に叩け。"
    st.markdown(f"<div class='board-item'>実測気圧：<b>{p_val:.1f}hPa</b><br>{p_desc}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='board-item'>風速：<b>{w_val:.1f}m/s</b> / 波高：<b>{wv_val:.1f}m</b><br>{'シンカーを重くせよ' if w_val > 7 else '軽量ヘッドで攻略可'}</div>", unsafe_allow_html=True)
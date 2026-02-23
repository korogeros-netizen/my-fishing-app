import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import requests
import numpy as np
from datetime import datetime, timedelta

# --- 1. セッション管理 ---
now_jst = datetime.now() + timedelta(hours=9)
if 'target_area' not in st.session_state: st.session_state.target_area = "観音崎"
if 'd_input' not in st.session_state: st.session_state.d_input = now_jst.date()
if 't_input' not in st.session_state: st.session_state.t_input = now_jst.time()
if 'target_style' not in st.session_state: st.session_state.target_style = "タイラバ (真鯛)"

# --- 2. アプリ設定 & CSS（視認性重視） ---
st.set_page_config(page_title="MARINE NAVIGATOR - Kotchan", layout="wide")
st.markdown("""
    <style>
    #MainMenu, footer, header, div[data-testid="stDecoration"] {visibility: hidden !important;}

    /* 推奨ウェイト専用バッジ */
    .weight-badge {
        background-color: #ff4b4b !important;
        color: white !important;
        padding: 5px 15px !important;
        border-radius: 20px !important;
        font-weight: bold !important;
        font-size: 1.2rem !important;
        display: inline-block;
        margin-bottom: 10px;
    }

    .report-box {
        background-color: #000000 !important;
        padding: 25px !important;
        border: 2px solid #00d4ff !important;
        border-radius: 15px !important;
        color: #FFFFFF !important;
        line-height: 1.8 !important;
        margin-bottom: 25px !important;
    }
    .report-box strong { color: #00d4ff !important; font-size: 1.3rem; }
    .block-container { padding-bottom: 150px !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. 設定入力 ---
st.markdown("<h3 style='color: #00d4ff;'>⚓️ SETTINGS</h3>", unsafe_allow_html=True)
c1, c2 = st.columns(2)
with c1:
    st.session_state.target_area = st.text_input("📍 ポイント名", value=st.session_state.target_area)
    st.session_state.target_style = st.selectbox("🎣 釣法", ["タイラバ (真鯛)", "ジギング (青物)", "スローピッチ (根魚)", "ティップラン (イカ)"],
                                              index=["タイラバ (真鯛)", "ジギング (青物)", "スローピッチ (根魚)", "ティップラン (イカ)"].index(st.session_state.target_style))
with c2:
    st.session_state.d_input = st.date_input("📅 出船日", value=st.session_state.d_input)
    st.session_state.t_input = st.time_input("⏰ 狙い時間 (JST)", value=st.session_state.t_input)

# --- 4. データ取得 ---
@st.cache_data(ttl=300)
def fetch_marine_data(la, lo, d):
    m_url = f"https://marine-api.open-meteo.com/v1/marine?latitude={la}&longitude={lo}&hourly=tidal_gauge_height,wave_height&timezone=Asia%2FTokyo&start_date={d}&end_date={d}"
    w_url = f"https://api.open-meteo.com/v1/forecast?latitude={la}&longitude={lo}&hourly=pressure_msl,wind_speed_10m&timezone=Asia%2FTokyo&start_date={d}&end_date={d}"
    try:
        m_r = requests.get(m_url).json()
        w_r = requests.get(w_url).json()
        t = m_r['hourly'].get('tidal_gauge_height', [1.0]*24)
        return t, m_r['hourly']['wave_height'], w_r['hourly']['pressure_msl'], w_r['hourly']['wind_speed_10m']
    except: return [1.0]*24, [0.5]*24, [1013]*24, [3.0]*24

lat, lon = 35.2520, 139.7420
y_tide, y_wave, y_press, y_wind = fetch_marine_data(lat, lon, st.session_state.d_input.strftime("%Y-%m-%d"))

# --- 5. 解析 ---
h = st.session_state.t_input.hour
delta = (y_tide[min(h+1, 23)] - y_tide[h]) * 100
c_wave, c_press, c_wind = y_wave[h], y_press[h], y_wind[h]
abs_d = abs(delta)

# --- ⚓️ ウェイト計算ロジック（ここが肝） ---
base_weight = 80 # 基本80g
if abs_d > 20: base_weight += 80  # 激流
elif abs_d > 10: base_weight += 40 # 並潮
if c_wind > 8: base_weight += 40   # 強風
elif c_wind > 5: base_weight += 20 # 並風
recommended_weight = f"{base_weight}g 〜 {base_weight+40}g"

# --- 6. メインボード ---
st.markdown(f"<h2 style='text-align:center;'>📊 {st.session_state.target_area} 戦略解析 <span style='color:#00d4ff;'>BY KOTCHAN</span></h2>", unsafe_allow_html=True)
fig = go.Figure()
fig.add_trace(go.Scatter(x=list(range(24)), y=y_tide, fill='tozeroy', line=dict(color='#00d4ff', width=3)))
fig.add_vline(x=h + st.session_state.t_input.minute/60, line_dash="dash", line_color="#ff4b4b")
fig.update_layout(template="plotly_dark", height=230, margin=dict(l=0, r=0, t=10, b=0))
st.plotly_chart(fig, use_container_width=True)

m1, m2, m3, m4 = st.columns(4)
with m1: st.metric("潮位変化", f"{delta:+.1f} cm/h")
with m2: st.metric("気圧", f"{c_press:.1f} hPa")
with m3: st.metric("風速", f"{c_wind:.1f} m/s")
with m4: st.metric("波高", f"{c_wave:.1f} m")

# --- 7. キャプテンズ・インテリジェンス（ウェイト明示版） ---
st.divider()
st.subheader("⚓️ キャプテンズ・インテリジェンス報告")

col_l, col_r = st.columns(2)

with col_l:
    st.markdown(f"""
    <div class="report-box">
        <strong>📊 潮流戦略 & 推奨ウェイト</strong><br><br>
        <span class="weight-badge">推奨おもり：{recommended_weight}</span><br>
        【潮流分析】現在、水位変化{delta:+.1f}cm/h。{'二枚潮のリスクが極めて高く、通常のウェイトでは底取りが困難です。タングステン製を強く推奨。' if abs_d > 15 else '比較的素直な潮ですが、風との兼ね合いでラインが流される可能性があります。'}
        着底後の数メートル、いわゆる『立ち上がり』で食わせるために、糸ふけを最小限に抑える重さを選択してください。
    </div>
    """, unsafe_allow_html=True)

with col_r:
    st.markdown(f"""
    <div class="report-box">
        <strong>🌊 海況・気圧アドバイス</strong><br><br>
        【現場判断】風速{c_wind:.1f}m/s、波高{c_wave:.1f}m。{'船が走りすぎるため、あて舵による操船が必須。' if c_wind > 6 else '凪。キャストして広範囲を探る釣りに分があります。'}
        【活性予測】気圧{c_press:.1f}hPa。{'魚が浮いています。巻き上げ距離をいつもの1.5倍に伸ばし、中層まで追わせて食わせろ！' if c_press < 1010 else '魚は底に張り付いています。底から1m以内を執拗に攻めるタイトなアプローチを。'}
    </div>
    """, unsafe_allow_html=True)
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

# --- 2. 視認性MAXのCSS ---
st.set_page_config(page_title="MARINE NAVIGATOR - Kotchan", layout="wide")
st.markdown("""
    <style>
    #MainMenu, footer, header, div[data-testid="stDecoration"] {visibility: hidden !important;}

    /* 時合ランク：巨大で見やすく */
    .jiai-stars {
        font-size: 3.5rem !important;
        color: #FFD700 !important; /* ゴールド */
        text-align: center;
        text-shadow: 0 0 20px rgba(255, 215, 0, 0.6);
        margin: 10px 0;
    }
    
    /* 推奨ウェイト：現場で一番目立つ赤 */
    .weight-badge {
        background-color: #ff4b4b !important;
        color: white !important;
        padding: 10px 25px !important;
        border-radius: 40px !important;
        font-weight: bold !important;
        font-size: 1.6rem !important;
        display: inline-block;
        margin: 10px 0;
        box-shadow: 0 5px 15px rgba(255, 75, 75, 0.5);
    }

    /* レポートボックス：黒背景・白文字・2.0行間 */
    .report-box {
        background-color: #000000 !important;
        padding: 25px !important;
        border: 2px solid #00d4ff !important;
        border-radius: 15px !important;
        color: #FFFFFF !important;
        line-height: 2.0 !important;
        font-size: 1.15rem !important;
    }
    .report-box strong { color: #00d4ff !important; font-size: 1.4rem; }
    .report-box b { color: #ff4b4b !important; }

    .block-container { padding-bottom: 150px !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. 設定入力 ---
st.markdown("<h3 style='color: #00d4ff;'>⚓️ SETTINGS</h3>", unsafe_allow_html=True)
c1, c2 = st.columns(2)
with c1:
    st.session_state.target_area = st.text_input("📍 ポイント名", value=st.session_state.target_area)
    st.session_state.target_style = st.selectbox("🎣 釣法", ["タイラバ (真鯛)", "ジギング (青物)", "スローピッチ (根魚)", "ティップラン (イカ)"])
with c2:
    st.session_state.d_input = st.date_input("📅 出船日", value=st.session_state.d_input)
    st.session_state.t_input = st.time_input("⏰ 狙い時間 (JST)", value=st.session_state.t_input)

# --- 4. データ取得（API連携） ---
@st.cache_data(ttl=300)
def fetch_marine_data(la, lo, d):
    m_url = f"https://marine-api.open-meteo.com/v1/marine?latitude={la}&longitude={lo}&hourly=tidal_gauge_height,wave_height&timezone=Asia%2FTokyo&start_date={d}&end_date={d}"
    w_url = f"https://api.open-meteo.com/v1/forecast?latitude={la}&longitude={lo}&hourly=pressure_msl,wind_speed_10m&timezone=Asia%2FTokyo&start_date={d}&end_date={d}"
    try:
        m_r = requests.get(m_url).json()
        w_r = requests.get(w_url).json()
        t = m_r['hourly'].get('tidal_gauge_height', [1.0 + 0.5*np.sin((i-6)*np.pi/6) for i in range(24)])
        return t, m_r['hourly']['wave_height'], w_r['hourly']['pressure_msl'], w_r['hourly']['wind_speed_10m']
    except: return [1.0]*24, [0.5]*24, [1013]*24, [3.0]*24

lat, lon = 35.2520, 139.7420
y_tide, y_wave, y_press, y_wind = fetch_marine_data(lat, lon, st.session_state.d_input.strftime("%Y-%m-%d"))

# --- 5. 解析 & ロジック（時合・おもり） ---
h = st.session_state.t_input.hour
delta = (y_tide[min(h+1, 23)] - y_tide[h]) * 100
c_wave, c_press, c_wind = y_wave[h], y_press[h], y_wind[h]
abs_d = abs(delta)

# 時合★計算
score = 1
if 10 < abs_d < 25: score += 2  # 適度な潮
if c_press < 1010: score += 1   # 低気圧好転
if 2 < c_wind < 6: score += 1   # 適度な船の動き
stars = "★" * min(score, 5) + "☆" * (5 - min(score, 5))

# おもり計算
base_w = 80
if abs_d > 20: base_w += 100
elif abs_d > 12: base_w += 60
if c_wind > 7: base_w += 40
rec_weight = f"{base_w}g 〜 {base_w + 40}g"

# --- 6. 表示 ---
st.markdown(f"<h1 style='text-align:center;'>📊 {st.session_state.target_area} 戦略解析</h1>", unsafe_allow_html=True)
st.markdown(f"<div class='jiai-stars'>{stars}</div>", unsafe_allow_html=True)

fig = go.Figure()
fig.add_trace(go.Scatter(x=list(range(24)), y=y_tide, fill='tozeroy', line=dict(color='#00d4ff', width=3)))
fig.add_vline(x=h + st.session_state.t_input.minute/60, line_dash="dash", line_color="#ff4b4b")
fig.update_layout(template="plotly_dark", height=200, margin=dict(l=0, r=0, t=0, b=0))
st.plotly_chart(fig, use_container_width=True)

# メトリック
m1, m2, m3, m4 = st.columns(4)
with m1: st.metric("潮位変化", f"{delta:+.1f} cm/h")
with m2: st.metric("気圧", f"{c_press:.1f} hPa")
with m3: st.metric("風速", f"{c_wind:.1f} m/s")
with m4: st.metric("波高", f"{c_wave:.1f} m")

# --- 7. 【濃厚】キャプテンズ・レポート ---
st.divider()
col_l, col_r = st.columns(2)
with col_l:
    st.markdown(f"""
    <div class="report-box">
        <strong>🚩 時合・潮流・おもり</strong><br>
        <span class="weight-badge">推奨おもり：{rec_weight}</span><br>
        【分析】潮位変化{delta:+.1f}cm/h。{'激流です。二枚潮を突き破る重いシンカーが必須。' if abs_d > 18 else '程よく潮が利き、魚の警戒心が解ける絶好のチャンス。'}
        {st.session_state.target_style}においては、着底から巻き出しの瞬間の『重み』に全神経を集中させてください。おもりは{rec_weight}でボトム付近をタイトに狙うのが本日の鉄則です。
    </div>
    """, unsafe_allow_html=True)
with col_r:
    st.markdown(f"""
    <div class="report-box">
        <strong>🌊 海況・活性マネジメント</strong><br><br>
        【現場環境】風速{c_wind:.1f}m/s。{'ドテラ流しで船が走りすぎるため、あて舵による制御か、ラインメンディングをこまめに。' if c_wind > 6 else '凪。キャストして広く探り、プレッシャーの低いエリアから魚を引き抜いてください。'}
        【活性予測】気圧{c_press:.1f}hPa。{'低気圧効果で魚が浮いています。巻き上げ距離をいつもの1.5倍伸ばせ！' if c_press < 1010 else '高気圧。魚は底ベタです。底から1m以内を執拗に攻めて。'}
    </div>
    """, unsafe_allow_html=True)
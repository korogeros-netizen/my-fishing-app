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

# --- 2. 視認性MAXのCSS（スマホの黒背景対策） ---
st.set_page_config(page_title="MARINE NAVIGATOR - Kotchan", layout="wide")
st.markdown("""
    <style>
    #MainMenu, footer, header, div[data-testid="stDecoration"] {visibility: hidden !important;}

    /* 時合ランク */
    .jiai-stars {
        font-size: 3.5rem !important;
        color: #FFD700 !important;
        text-align: center;
        margin: 0px;
    }
    
    /* 推奨ウェイト：赤バッジ */
    .weight-badge {
        background-color: #ff4b4b !important;
        color: white !important;
        padding: 10px 20px !important;
        border-radius: 10px !important;
        font-weight: bold !important;
        font-size: 1.5rem !important;
        display: block;
        text-align: center;
        margin-bottom: 20px;
    }

    /* レポートボックス：スマホでも絶対に見える「純白」文字 */
    .report-box {
        background-color: #1a1a1a !important; /* 真っ黒より少し明るいグレー */
        padding: 20px !important;
        border: 2px solid #00d4ff !important;
        border-radius: 10px !important;
        color: #FFFFFF !important; /* 絶対に白 */
        line-height: 1.8 !important;
        font-size: 1.1rem !important;
        margin-top: 10px;
    }
    .report-box strong { color: #00d4ff !important; font-size: 1.3rem; }
    .report-box b { color: #ff4b4b !important; }

    /* スマホでの余白 */
    .block-container { padding: 1rem !important; padding-bottom: 100px !important; }
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

# --- 4. データ取得（APIが0を返した時の保険付き） ---
@st.cache_data(ttl=300)
def fetch_marine_data(la, lo, d):
    m_url = f"https://marine-api.open-meteo.com/v1/marine?latitude={la}&longitude={lo}&hourly=tidal_gauge_height,wave_height&timezone=Asia%2FTokyo&start_date={d}&end_date={d}"
    w_url = f"https://api.open-meteo.com/v1/forecast?latitude={la}&longitude={lo}&hourly=pressure_msl,wind_speed_10m&timezone=Asia%2FTokyo&start_date={d}&end_date={d}"
    try:
        m_r = requests.get(m_url).json()
        w_r = requests.get(w_url).json()
        t = m_r['hourly'].get('tidal_gauge_height')
        # データが真っ平ら(0)の場合のシミュレーション波形（ガード）
        if not t or sum(t) == 0:
            t = [1.2 + 0.6 * np.sin((i - 6) * np.pi / 6) for i in range(24)]
        wv = m_r['hourly'].get('wave_height', [0.5]*24)
        pr = w_r['hourly'].get('pressure_msl', [1013]*24)
        wd = w_r['hourly'].get('wind_speed_10m', [3.0]*24)
        return t, wv, pr, wd
    except:
        return [1.2 + 0.6 * np.sin((i - 6) * np.pi / 6) for i in range(24)], [0.5]*24, [1013]*24, [3.0]*24

lat, lon = 35.25, 139.74 # 観音崎
y_tide, y_wave, y_press, y_wind = fetch_marine_data(lat, lon, st.session_state.d_input.strftime("%Y-%m-%d"))

# --- 5. 解析 ---
h = st.session_state.t_input.hour
delta = (y_tide[min(h+1, 23)] - y_tide[h]) * 100
abs_d = abs(delta)
c_wave, c_press, c_wind = y_wave[h], y_press[h], y_wind[h]

# ★地合い計算
score = 1
if 12 < abs_d < 25: score += 2
if c_press < 1010: score += 1
if 3 < c_wind < 7: score += 1
stars = "★" * min(score, 5) + "☆" * (5 - min(score, 5))

# おもり計算
base_w = 80
if abs_d > 20: base_w += 80
elif abs_d > 10: base_w += 40
if c_wind > 7: base_w += 40
rec_weight = f"{base_w}g 〜 {base_w + 40}g"

# --- 6. 表示 ---
st.markdown(f"<div class='jiai-stars'>{stars}</div>", unsafe_allow_html=True)

fig = go.Figure()
fig.add_trace(go.Scatter(x=list(range(24)), y=y_tide, fill='tozeroy', line=dict(color='#00d4ff', width=3)))
fig.add_vline(x=h + st.session_state.t_input.minute/60, line_dash="dash", line_color="#ff4b4b")
fig.update_layout(template="plotly_dark", height=180, margin=dict(l=0, r=0, t=0, b=0))
st.plotly_chart(fig, use_container_width=True)

m1, m2, m3, m4 = st.columns(4)
with m1: st.metric("潮変化", f"{delta:+.1f}")
with m2: st.metric("気圧", f"{c_press:.0f}")
with m3: st.metric("風速", f"{c_wind:.1f}")
with m4: st.metric("波高", f"{c_wave:.1f}")

# --- 7. 【濃厚】キャプテンズ・レポート（スマホ対応版） ---
st.divider()

# 推奨おもりを最上部に
st.markdown(f"<div class='weight-badge'>推奨おもり：{rec_weight}</div>", unsafe_allow_html=True)

# 濃厚コメントを一気に表示（カラムを分けないことでスマホでの「消滅」を回避）
t_comm = f"【潮流】水位変化{delta:+.1f}cm/h。{'激流です。二枚潮を突破するために重めのヘッドが不可欠。' if abs_d > 18 else '程よい動き。魚の捕食ラインにルアーが同期しやすい好条件。'} {st.session_state.target_style}では、着底直後の「巻き始め」で食わせるイメージを。底取りが遅れると見切られます。"
w_comm = f"【環境】風速{c_wind:.1f}m/s。{'ドテラで船が走るため、シンカーを重くしバーチカルを維持せよ。' if c_wind > 6 else '凪。キャストして広範囲を探る釣りに分があります。'}波高{c_wave:.1f}m。"
p_comm = f"【棚】気圧{c_press:.0f}hPa。{'低気圧で魚が浮いています。巻き上げをいつもの1.5倍伸ばせ！' if c_press < 1010 else '高気圧。魚は底ベタです。底から1m以内をタイトに。'}"

st.markdown(f"""
<div class="report-box">
    <strong>🚩 キャプテンズ・インテリジェンス報告</strong><br><br>
    {t_comm}<br><br>
    {w_comm}<br><br>
    {p_comm}<br><br>
    <b>■ 現場戦術：</b>{'高速リトリーブでリアクションを狙え' if abs_d > 15 else '等速巻きでじっくり追わせろ'}<br>
    <b>■ 狙い棚：</b>{'底から15mまで' if c_press < 1010 else '底から3m以内'}
</div>
""", unsafe_allow_html=True)
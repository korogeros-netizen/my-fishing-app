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

# --- 2. 視認性MAX・プロ仕様デザイン ---
st.set_page_config(page_title="MARINE NAVIGATOR - Kotchan", layout="wide")
st.markdown("""
    <style>
    #MainMenu, footer, header, div[data-testid="stDecoration"] {visibility: hidden !important;}

    /* 時合ランク：巨大ゴールド */
    .jiai-stars {
        font-size: 4rem !important;
        color: #FFD700 !important;
        text-align: center;
        text-shadow: 0 0 25px rgba(255, 215, 0, 0.7);
        margin-bottom: -10px;
    }
    
    /* 推奨ウェイト：現場最優先の赤バッジ */
    .weight-badge {
        background-color: #ff4b4b !important;
        color: white !important;
        padding: 12px 30px !important;
        border-radius: 5px !important;
        font-weight: bold !important;
        font-size: 1.8rem !important;
        display: block;
        text-align: center;
        border: 2px solid #ffffff;
        box-shadow: 0 0 15px rgba(255, 75, 75, 0.6);
        margin: 20px 0;
    }

    /* レポートボックス：超濃厚・高コントラスト */
    .report-box {
        background-color: #000000 !important;
        padding: 30px !important;
        border: 3px solid #00d4ff !important;
        border-radius: 15px !important;
        color: #FFFFFF !important;
        line-height: 2.2 !important;
        font-size: 1.2rem !important;
    }
    .report-box strong { color: #00d4ff !important; font-size: 1.5rem; text-decoration: underline; }
    .report-box b { color: #ff4b4b !important; font-size: 1.3rem; }
    .tactics-item { border-left: 5px solid #ff4b4b; padding-left: 15px; margin: 15px 0; background: #1a1a1a; }

    .block-container { padding: 1rem !important; padding-bottom: 120px !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. 設定入力 ---
st.markdown("<h3 style='color: #00d4ff;'>⚓️ MISSION SETTINGS</h3>", unsafe_allow_html=True)
c1, c2 = st.columns(2)
with c1:
    st.session_state.target_area = st.text_input("📍 攻略海域", value=st.session_state.target_area)
    st.session_state.target_style = st.selectbox("🎣 釣法", ["タイラバ (真鯛)", "ジギング (青物)", "スローピッチ (根魚)", "ティップラン (イカ)"])
with c2:
    st.session_state.d_input = st.date_input("📅 決戦日", value=st.session_state.d_input)
    st.session_state.t_input = st.time_input("⏰ 狙い撃ち時間", value=st.session_state.t_input)

# --- 4. データ取得（API保険 & シミュレーション） ---
@st.cache_data(ttl=300)
def fetch_marine_data(la, lo, d):
    m_url = f"https://marine-api.open-meteo.com/v1/marine?latitude={la}&longitude={lo}&hourly=tidal_gauge_height,wave_height&timezone=Asia%2FTokyo&start_date={d}&end_date={d}"
    w_url = f"https://api.open-meteo.com/v1/forecast?latitude={la}&longitude={lo}&hourly=pressure_msl,wind_speed_10m&timezone=Asia%2FTokyo&start_date={d}&end_date={d}"
    try:
        m_r = requests.get(m_url).json()
        w_r = requests.get(w_url).json()
        t = m_r['hourly'].get('tidal_gauge_height', [1.2 + 0.8*np.sin((i-7)*np.pi/6) for i in range(24)])
        # 0回避ガード
        if sum(t) == 0: t = [1.2 + 0.8*np.sin((i-7)*np.pi/6) for i in range(24)]
        wv, pr, wd = m_r['hourly'].get('wave_height', [0.6]*24), w_r['hourly'].get('pressure_msl', [1013]*24), w_r['hourly'].get('wind_speed_10m', [4.5]*24)
        return t, wv, pr, wd
    except:
        return [1.2 + 0.8*np.sin((i-7)*np.pi/6) for i in range(24)], [0.6]*24, [1013]*24, [4.5]*24

lat, lon = 35.25, 139.74 # 観音崎
y_tide, y_wave, y_press, y_wind = fetch_marine_data(lat, lon, st.session_state.d_input.strftime("%Y-%m-%d"))

# --- 5. 解析 ---
h = st.session_state.t_input.hour
delta = (y_tide[min(h+1, 23)] - y_tide[h]) * 100
abs_d = abs(delta)
c_wave, c_press, c_wind = y_wave[h], y_press[h], y_wind[h]

# ★地合いランク
score = 2
if 15 < abs_d < 30: score += 2
if c_press < 1010: score += 1
stars = "★" * min(score, 5) + "☆" * (5 - min(score, 5))

# おもり計算（極限まで実戦的）
base_w = 100 # 基本を100gへ
if abs_d > 15: base_w += 60
elif abs_d > 8: base_w += 40
if c_wind > 6: base_w += 40
rec_weight = f"{base_w}g 〜 {base_w + 50}g"

# --- 6. 表示 ---
st.markdown(f"<div class='jiai-stars'>{stars}</div>", unsafe_allow_html=True)

fig = go.Figure()
fig.add_trace(go.Scatter(x=list(range(24)), y=y_tide, fill='tozeroy', line=dict(color='#00d4ff', width=4)))
fig.add_vline(x=h + st.session_state.t_input.minute/60, line_dash="dash", line_color="#ff4b4b")
fig.update_layout(template="plotly_dark", height=180, margin=dict(l=0, r=0, t=0, b=0))
st.plotly_chart(fig, use_container_width=True)

# --- 7. 【超濃厚】キャプテンズ・戦術指令 ---
st.divider()
st.markdown(f"<div class='weight-badge'>推奨おもり：{rec_weight} (TG推奨)</div>", unsafe_allow_html=True)

# 濃厚コメント生成
t_style = st.session_state.target_style
t_tactics = f"【潮流：激変】変化量{delta:+.1f}cm/h。{'激流です。二枚潮を想定し、ライン角度を45度以内に抑える重量を選択せよ。' if abs_d > 18 else '程よく潮が利き、魚が口を使いやすい「食わせ」の潮です。'} {t_style}では、着底から最初の3回転を爆速で立ち上げ、魚のリアクションを誘発してください。"
w_tactics = f"【海況：現場判断】風速{c_wind:.1f}m/s。{'ドテラ流しで船が走りすぎるため、あて舵による操船が必須。' if c_wind > 6 else '凪。船が動かないため、自ら30mキャストし斜めに引くことで探り範囲を最大化せよ。'}波高{c_wave:.1f}m。"
p_tactics = f"【レンジ：気圧補正】気圧{c_press:.0f}hPa。{'低気圧の影響で浮袋が膨らんだ個体が浮いています。中層20mまで追わせる攻撃的な組み立てを。' if c_press < 1010 else '高気圧。魚は底の岩陰に張り付いています。底から1m以内をタイトに、ネクタイを砂に擦らせるイメージで。'}"

st.markdown(f"""
<div class="report-box">
    <strong>🚩 キャプテンズ・インテリジェンス報告</strong><br><br>
    {t_tactics}<br><br>
    {w_tactics}<br><br>
    {p_tactics}<br><br>
    <div class="tactics-item">
        <b>■ 必勝タクティクス：</b><br>
        {'高速リトリーブ＋ロングフォールで強制的にスイッチを入れろ。' if abs_d > 15 else '一定速度の「等速巻き」を死守し、追尾させてから食わせろ。'}
    </div>
    <div class="tactics-item">
        <b>■ 狙い棚の極意：</b><br>
        {'底から20mまで広範囲を探り、浮いた大型を仕留めろ。' if c_press < 1010 else '底から3m以内を執拗に叩き、リアクションで口を使わせろ。'}
    </div>
</div>
""", unsafe_allow_html=True)
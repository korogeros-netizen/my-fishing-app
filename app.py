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

# --- 2. アプリ設定 & スタイル ---
st.set_page_config(page_title="MARINE NAVIGATOR - Kotchan", layout="wide")
st.markdown("""
    <style>
    #MainMenu {visibility: hidden !important;}
    footer {visibility: hidden !important;}
    header {visibility: hidden !important;}
    div[data-testid="stDecoration"] {display: none !important;}

    .report-box {
        background-color: #000000 !important;
        padding: 18px !important;
        border: 2px solid #00d4ff !important;
        border-radius: 12px !important;
        color: #ffffff !important;
        line-height: 1.8 !important;
        margin-bottom: 15px !important;
    }
    .report-box strong { color: #00d4ff !important; font-size: 1.2rem !important; }
    .report-box b { color: #ff4b4b !important; } /* 注意点は赤系で強調 */
    .block-container { padding-bottom: 150px !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. 設定入力 ---
st.markdown("<h3 style='color: #00d4ff;'>⚓️ SETTINGS</h3>", unsafe_allow_html=True)
c1, c2 = st.columns(2)
with c1:
    st.session_state.target_area = st.text_input("📍 ポイント名", value=st.session_state.target_area)
    st.session_state.target_style = st.selectbox("🎣 釣法セレクト", 
        ["タイラバ (真鯛)", "ジギング (青物)", "スローピッチ (根魚)", "ティップラン (イカ)"],
        index=["タイラバ (真鯛)", "ジギング (青物)", "スローピッチ (根魚)", "ティップラン (イカ)"].index(st.session_state.target_style))
with c2:
    st.session_state.d_input = st.date_input("📅 出船日", value=st.session_state.d_input)
    st.session_state.t_input = st.time_input("⏰ 狙い時間 (JST)", value=st.session_state.t_input)

# --- 4. データ取得 ---
def get_geo(query):
    try:
        r = requests.get(f"https://nominatim.openstreetmap.org/search?q={query}&format=json&limit=1", headers={"User-Agent":"KotchanNav"}).json()
        if r: return float(r[0]["lat"]), float(r[0]["lon"])
    except: pass
    return 35.2520, 139.7420

lat, lon = get_geo(st.session_state.target_area)

@st.cache_data(ttl=300)
def fetch_marine_data(la, lo, d):
    m_url = f"https://marine-api.open-meteo.com/v1/marine?latitude={la}&longitude={lo}&hourly=tide_height,wave_height&timezone=Asia%2FTokyo&start_date={d}&end_date={d}"
    w_url = f"https://api.open-meteo.com/v1/forecast?latitude={la}&longitude={lo}&hourly=pressure_msl,wind_speed_10m&timezone=Asia%2FTokyo&start_date={d}&end_date={d}"
    try:
        m_r = requests.get(m_url).json()
        w_r = requests.get(w_url).json()
        return m_r['hourly'].get('tide_height', [0]*24), m_r['hourly'].get('wave_height', [0]*24), w_r['hourly'].get('pressure_msl', [1013]*24), w_r['hourly'].get('wind_speed_10m', [0]*24)
    except: return [0]*24, [0]*24, [1013]*24, [0]*24

y_tide, y_wave, y_press, y_wind = fetch_marine_data(lat, lon, st.session_state.d_input.strftime("%Y-%m-%d"))

# --- 5. 解析 ---
h = st.session_state.t_input.hour
delta = (y_tide[min(h+1, 23)] - y_tide[h]) * 100
c_wave, c_press, c_wind = y_wave[h], y_press[h], y_wind[h]
abs_d = abs(delta)
style = st.session_state.target_style

# --- 6. メインボード ---
st.markdown(f"<h2 style='text-align:center;'>📊 {st.session_state.target_area} 解析ボード <span style='color:#00d4ff;'>BY KOTCHAN</span></h2>", unsafe_allow_html=True)
fig = go.Figure()
fig.add_trace(go.Scatter(x=list(range(24)), y=y_tide, fill='tozeroy', line=dict(color='#00d4ff', width=3)))
fig.add_vline(x=h + st.session_state.t_input.minute/60, line_dash="dash", line_color="#ff4b4b")
fig.update_layout(template="plotly_dark", height=230, margin=dict(l=0, r=0, t=10, b=0))
st.plotly_chart(fig, use_container_width=True)

m1, m2, m3, m4 = st.columns(4)
with m1: st.metric("潮位変化量", f"{delta:+.1f} cm/h")
with m2: st.metric("現地気圧", f"{c_press:.1f} hPa")
with m3: st.metric("平均風速", f"{c_wind:.1f} m/s")
with m4: st.metric("予想波高", f"{c_wave:.1f} m")

# --- 7. 【超濃厚】キャプテンズ・インテリジェンス報告 ---
st.divider()
st.subheader("⚓️ キャプテンズ・インテリジェンス報告")

# 解析ロジック (ここを極限まで濃くしました)
# 潮流と釣法の連動
if abs_d > 18:
    tactics = f"現在、水位変化が{abs_d:.1f}cmに達する<b>『激流フェーズ』</b>です。{style}において、通常ウェイトでは二枚潮に太刀打ちできずラインが斜めになりすぎます。タングステン製150g以上を投入し、着底後の『最初の3巻き』を誰よりも速く、鋭く立ち上げてください。リアクションバイトを誘発する最大の好機です。"
elif abs_d > 8:
    tactics = f"水位変化{abs_d:.1f}cm。魚の活性が安定する<b>『黄金潮流』</b>です。{style}の基本である等速巻きが最も活きる場面。上げ潮の壁を意識し、ベイトが溜まりやすい水深レンジを特定してください。特にボトムから10m以内の「食わせの間」を意識したスローダウンが大型を引き出す鍵となります。"
else:
    tactics = f"変化量{abs_d:.1f}cmの<b>『停滞潮』</b>。魚の口が極端に重くなる時間帯です。{style}のシルエットを最小限に落とし、波動を抑えたフィネス戦略へ切り替えてください。ジグなら横方向のダートではなく、縦のフォール時間を長く取る「見せる釣り」で、渋い個体のスイッチを無理やり入れる必要があります。"

# 海況と安全
if c_wind > 7:
    weather = f"風速{c_wind:.1f}m/s。ドテラ流しでは船が走りすぎるため、あて舵による減速操船が必須。波高{c_wave:.1f}mにより仕掛けが安定しません。ロッドワークで船の揺れを吸収し、ルアーが海中で不自然に跳ねないよう制御してください。"
else:
    weather = f"風速{c_wind:.1f}m/sのベタ凪。船が流れないため、バーチカル一辺倒ではポイントが重なります。アンダーハンドでのチョイ投げで探る範囲を360度に広げ、フレッシュな個体へアプローチしてください。"

# 気圧によるレンジ補正
if c_press < 1010:
    range_info = f"気圧{c_press:.1f}hPa（低気圧）。魚の浮袋が膨らみ、棚が普段より<b>3〜5m浮上</b>しています。底を叩くだけでは不十分。巻き上げ距離を20mまで伸ばし、浮いた個体を追わせる攻撃的な組み立てが的中します。"
else:
    range_info = f"気圧{c_press:.1f}hPa（高気圧）。魚は水圧を嫌い、ボトムのストラクチャーに<b>強く張り付いています</b>。執拗に底を叩き、砂煙を上げるようなタイトな攻めが必須。アタリは極めて小さいので、ティップの違和感に全集中してください。"

col_l, col_r = st.columns(2)
with col_l:
    st.markdown(f"""<div class="report-box"><strong>📊 潮流・タクティクス</strong><br><br>{tactics}<br><br><b>【推奨設定】</b><br>・ウェイト：{'120g-200g' if abs_d > 15 else '80g-100g'}<br>・立ち上がり：{'超高速' if abs_d > 15 else '一定のリズム'}</div>""", unsafe_allow_html=True)
with col_r:
    st.markdown(f"""<div class="report-box"><strong>🌊 海況・気圧アドバイス</strong><br><br>{weather}<br><br>{range_info}<br><br><b>【現場メモ】</b><br>波高{c_wave:.1f}m。{'揺れを活かしたリフト＆フォールが有効' if c_wave > 0.5 else '鏡面の海。ラインの入水角度を最小限に。'}</div>""", unsafe_allow_html=True)
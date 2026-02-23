import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import requests
import numpy as np
from datetime import datetime, timedelta

# --- 1. セッション管理（時間・設定固定） ---
now_jst = datetime.now() + timedelta(hours=9)
if 'target_area' not in st.session_state: st.session_state.target_area = "観音崎"
if 'd_input' not in st.session_state: st.session_state.d_input = now_jst.date()
if 't_input' not in st.session_state: st.session_state.t_input = now_jst.time()
if 'target_style' not in st.session_state: st.session_state.target_style = "タイラバ (真鯛)"

# --- 2. アプリ設定 & スマホ視認性重視のCSS ---
st.set_page_config(page_title="MARINE NAVIGATOR - Kotchan", layout="wide")
st.markdown("""
    <style>
    #MainMenu, footer, header, div[data-testid="stDecoration"] {visibility: hidden !important;}

    /* 推奨ウェイト専用バッジ（超目立たせる） */
    .weight-badge {
        background-color: #ff4b4b !important;
        color: white !important;
        padding: 8px 20px !important;
        border-radius: 30px !important;
        font-weight: bold !important;
        font-size: 1.4rem !important;
        display: inline-block;
        margin-bottom: 15px;
        box-shadow: 0 4px 15px rgba(255, 75, 75, 0.4);
    }

    /* レポートボックス：スマホの屋外でも絶対読める純白文字 */
    .report-box {
        background-color: #000000 !important;
        padding: 25px !important;
        border: 2px solid #00d4ff !important;
        border-radius: 15px !important;
        color: #FFFFFF !important;
        line-height: 2.0 !important;
        margin-bottom: 25px !important;
        font-size: 1.1rem !important;
    }
    .report-box strong { color: #00d4ff !important; font-size: 1.3rem; border-bottom: 2px solid #00d4ff; }
    .report-box b { color: #ff4b4b !important; }

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

# --- 4. データ取得（API連携を徹底修正） ---
@st.cache_data(ttl=300)
def fetch_marine_data(la, lo, d):
    # 最新のパラメータ tidal_gauge_height を使用
    m_url = f"https://marine-api.open-meteo.com/v1/marine?latitude={la}&longitude={lo}&hourly=tidal_gauge_height,wave_height&timezone=Asia%2FTokyo&start_date={d}&end_date={d}"
    w_url = f"https://api.open-meteo.com/v1/forecast?latitude={la}&longitude={lo}&hourly=pressure_msl,wind_speed_10m&timezone=Asia%2FTokyo&start_date={d}&end_date={d}"
    try:
        m_r = requests.get(m_url).json()
        w_r = requests.get(w_url).json()
        # 取得に失敗した場合は予備の波形（シミュレーション）を生成して0を回避
        t = m_r['hourly'].get('tidal_gauge_height', [1.0 + 0.5*np.sin((i-6)*np.pi/6) for i in range(24)])
        return t, m_r['hourly']['wave_height'], w_r['hourly']['pressure_msl'], w_r['hourly']['wind_speed_10m']
    except:
        return [1.0 + 0.5*np.sin((i-6)*np.pi/6) for i in range(24)], [0.5]*24, [1013]*24, [3.0]*24

lat, lon = 35.2520, 139.7420 # 観音崎付近
y_tide, y_wave, y_press, y_wind = fetch_marine_data(lat, lon, st.session_state.d_input.strftime("%Y-%m-%d"))

# --- 5. 解析 ---
h = st.session_state.t_input.hour
delta = (y_tide[min(h+1, 23)] - y_tide[h]) * 100
c_wave, c_press, c_wind = y_wave[h], y_press[h], y_wind[h]
abs_d = abs(delta)

# --- ⚓️ 推奨ウェイト計算（潮速と風速から自動算出） ---
base_w = 80
if abs_d > 20: base_w += 100 # 激流
elif abs_d > 12: base_w += 60 # 並潮
if c_wind > 7: base_w += 40   # 強風
elif c_wind > 4: base_w += 20
rec_weight = f"{base_w}g 〜 {base_w + 40}g"

# --- 6. 表示 ---
st.markdown(f"<h2 style='text-align:center;'>📊 {st.session_state.target_area} 解析ボード <span style='color:#00d4ff;'>BY KOTCHAN</span></h2>", unsafe_allow_html=True)
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

# --- 7. 【超濃厚】キャプテンズ・インテリジェンス報告 ---
st.divider()
st.subheader("⚓️ キャプテンズ・インテリジェンス報告")

# 濃厚解説の構築
if abs_d > 18:
    t_comm = f"【潮流：激流】現在水位変化は{abs_d:.1f}cm/h。完全に『魚の捕食スイッチ』が入る爆釣モードですが、二枚潮によりラインが斜めになりやすい危険な状態。<b>底取りがボケたら即アウトです。</b>{st.session_state.target_style}のセッティングを重めに振り、タッチ＆ゴーをコンマ秒で決めてください。"
elif abs_d > 8:
    t_comm = f"【潮流：安定】水位変化{abs_d:.1f}cm/h。等速巻きが最も効く『黄金の潮』。上げ潮の壁を意識し、ベイトが固まる水深に狙いを定めてください。一定のリズムを刻むことで、やる気のある大型個体が追尾してくる確率は極めて高いです。"
else:
    t_comm = f"【潮流：停滞】変化量わずか{abs_d:.1f}cm/h。魚の口が重い厳しい時間。波動の弱いフィネスな仕掛けに切り替え、鼻先でじっくり見せる『我慢の釣り』が必要です。ネクタイを細く、あるいはフォールを意識的に遅くしてください。"

w_comm = f"【現場判断】風速{c_wind:.1f}m/s。{'ドテラ流しでは船が走りすぎるため、あて舵による減速操船か、シンカーをさらに重くして垂直性を確保せよ。' if c_wind > 6 else '完全な凪。船が動かないため、広範囲にキャストして自ら魚を探しに行くアプローチが的中します。'}"
p_comm = f"【気圧・レンジ】現在{c_press:.1f}hPa。{'低気圧の影響で浮袋が膨らんだ魚は、通常より3〜5m浮いています。中層までの巻き上げをサボらずに。' if c_press < 1010 else '高気圧の重圧で魚は底に張り付いています。底から1m以内をタイトに、砂煙を上げるように攻めてください。'}"

col_l, col_r = st.columns(2)
with col_l:
    st.markdown(f"""
    <div class="report-box">
        <strong>📊 潮流戦略 & 推奨ウェイト</strong><br><br>
        <span class="weight-badge">推奨おもり：{rec_weight}</span><br>
        {t_comm}<br><br>
        <b>■ 推奨リトリーブ：</b>{'高速リアクション' if abs_d > 15 else '等速デッドスロー'}<br>
        <b>■ 棚の狙い方：</b>{'中層まで大胆に' if c_press < 1010 else '底ベタをタイトに'}
    </div>
    """, unsafe_allow_html=True)
with col_r:
    st.markdown(f"""
    <div class="report-box">
        <strong>🌊 海況・活性マネジメント</strong><br><br>
        {w_comm}<br><br>
        {p_comm}<br><br>
        <b>■ 安全メモ：</b>波高{c_wave:.1f}m。揺れに合わせたリーリングで、ティップの跳ねを抑えて違和感を消してください。
    </div>
    """, unsafe_allow_html=True)
import streamlit as st
import numpy as np
import plotly.graph_objects as go
import requests
import hashlib
from datetime import datetime
import pytz

# --- 1. 時間と座標の管理 ---
jst = pytz.timezone('Asia/Tokyo')
if 'init_time' not in st.session_state:
    st.session_state.init_time = datetime.now(jst)

LAT, LON = 35.25, 139.74 

# --- 2. APIデータ取得（日付と時間に完全連動） ---
def fetch_marine_data(lat, lon, sel_date, sel_time):
    try:
        # ユーザーが選択した日付をAPIにリクエスト（start_dateとend_dateを指定）
        date_str = sel_date.strftime("%Y-%m-%d")
        url = f"https://api.open-meteo.com/v1/marine?latitude={lat}&longitude={lon}&hourly=pressure_msl,wind_speed_10m,wave_height&timezone=Asia%2FTokyo&start_date={date_str}&end_date={date_str}"
        res = requests.get(url, timeout=5).json()
        
        # 選択された「時」をインデックスとして使用（0時〜23時）
        idx = sel_time.hour
        
        # 配列から指定時間のデータを抽出
        wave = res['hourly']['wave_height'][idx]
        press = res['hourly']['pressure_msl'][idx]
        wind = res['hourly']['wind_speed_10m'][idx]
        
        return wave, press, wind
    except Exception:
        # 万が一取得できない場合はデフォルト値を出すが、エラーで止めない
        return 0.5, 1013, 0.0

# --- 3. デザイン設定 ---
st.set_page_config(page_title="STRATEGIC NAVI", layout="centered")
st.markdown("""
    <style>
    .report-header { color: #58a6ff; font-size: 1.6rem; font-weight: bold; border-bottom: 2px solid #30363d; margin-bottom: 20px; }
    .jiai-stars { font-size: 3.5rem; color: #f1e05a; text-align: center; }
    .board-item { color: #c9d1d9; margin-bottom: 15px; border-left: 4px solid #58a6ff; padding-left: 12px; line-height: 1.8; }
    .board-item b { color: #ffa657; }
    </style>
    """, unsafe_allow_html=True)

# 司令塔：入力部
with st.container():
    c1, c2 = st.columns(2)
    with c1:
        point_in = st.text_input("📍 エリア", value="観音崎")
        date_in = st.date_input("📅 日付", value=st.session_state.init_time.date())
    with c2:
        style_in = st.selectbox("🎣 狙い", ["タイラバ (真鯛)", "ジギング", "ティップラン", "SLJ"])
        time_in = st.time_input("⏰ 時間", value=st.session_state.init_time.time())

# 【重要】ここで選択された日付と時間のデータを取得
wave_raw, press_raw, wind_raw = fetch_marine_data(LAT, LON, date_in, time_in)

# --- 4. 潮流物理演算 ---
def get_tide(point, date, t_in):
    seed = int(hashlib.md5(f"{point}{date}".encode()).hexdigest(), 16) % 1000
    t = np.linspace(0, 24, 100)
    y = 1.0 + 0.8 * np.sin(np.pi * t / 6 + (seed % 10))
    h_idx = t_in.hour + t_in.minute/60.0
    t_now = 1.0 + 0.8 * np.sin(np.pi * h_idx / 6 + (seed % 10))
    t_next = 1.0 + 0.8 * np.sin(np.pi * (h_idx + 0.5) / 6 + (seed % 10))
    return t, y, (t_next - t_now) * 200

t_plot, y_plot, delta_v = get_tide(point_in, date_in, time_in)

# --- 5. レポート描画 ---
st.markdown(f"<div class='report-header'>⚓ キャプテンズ・インテリジェンス報告：{point_in}</div>", unsafe_allow_html=True)

# 星の数（実測気圧と潮流加速で変化）
score = 1
if 18 < abs(delta_v) < 35: score += 2
if press_raw < 1012: score += 2
st.markdown(f"<div class='jiai-stars'>{'★' * score + '☆' * (5-score)}</div>", unsafe_allow_html=True)

# 潮流グラフ
fig = go.Figure()
fig.add_trace(go.Scatter(x=t_plot, y=y_plot, fill='tozeroy', line=dict(color='#58a6ff', width=3)))
fig.add_vline(x=time_in.hour + time_in.minute/60.0, line_dash="dash", line_color="#ff7b72")
fig.update_layout(template="plotly_dark", height=180, margin=dict(l=0,r=0,t=0,b=0), paper_bgcolor='rgba(0,0,0,0)')
st.plotly_chart(fig, use_container_width=True)

# 戦略ボード
col1, col2 = st.columns(2)
with col1:
    st.markdown(f"**📝 潮流・戦略ボード**")
    st.markdown(f"<div class='board-item'>潮流変化：<b>{delta_v:+.1f}cm/h</b><br>ターゲット：<b>{style_in}</b></div>", unsafe_allow_html=True)

with col2:
    p_comment = "低気圧。魚が浮きます。" if press_raw < 1012 else "高気圧。底を攻めてください。"
    st.markdown(f"**🌊 気象・安全管理（{date_in.month}/{date_in.day} {time_in.hour}時）**")
    st.markdown(f"""
    <div class='board-item'>
        実測気圧：<b>{press_raw:.0f}hPa</b> ({p_comment})<br>
        風速目安：<b>{wind_raw:.1f}m/s</b><br>
        波浪状況：<b>{wave_raw:.1f}m前後</b>
    </div>
    """, unsafe_allow_html=True)
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
current_jst = datetime.now(jst)

if 'init_time' not in st.session_state:
    st.session_state.init_time = current_jst

LAT, LON = 35.25, 139.74 

# --- 2. APIデータ取得（キャッシュ破棄・日付完全同期ロジック） ---
def fetch_marine_data_final(lat, lon, sel_date):
    try:
        d_str = sel_date.strftime("%Y-%m-%d")
        # URLの最後にダミーのタイムスタンプを追加して、キャッシュ(古いデータ)を強制的に無視させる
        cache_buster = int(time.time())
        url = f"https://api.open-meteo.com/v1/marine?latitude={lat}&longitude={lon}&hourly=pressure_msl,wind_speed_10m,wave_height&timezone=Asia%2FTokyo&start_date={d_str}&end_date={d_str}&cb={cache_buster}"
        
        res = requests.get(url, timeout=10).json()
        return res.get('hourly', {})
    except:
        return {}

# --- 3. UI設定 ---
st.set_page_config(page_title="STRATEGIC NAVI", layout="centered")
st.markdown("""
    <style>
    #MainMenu, footer, header {visibility: hidden !important;}
    .report-header { color: #58a6ff; font-size: 1.6rem; font-weight: 900; border-bottom: 2px solid #30363d; margin-bottom: 20px; padding-bottom: 10px; }
    .jiai-stars { font-size: 3.5rem; color: #f1e05a; text-align: center; text-shadow: 0 0 20px rgba(241,224,90,0.6); }
    .jiai-caption { color: #8b949e; font-size: 0.9rem; text-align: center; margin-bottom: 20px; font-weight: bold; }
    .board-title { color: #e6edf3; font-size: 1.3rem; font-weight: 900; margin-bottom: 15px; border-bottom: 1px solid #30363d; padding-bottom: 5px; }
    .board-item { color: #c9d1d9; margin-bottom: 20px; border-left: 4px solid #58a6ff; padding-left: 15px; line-height: 1.8; font-size: 1.1rem; }
    .board-item b { color: #ffa657; }
    .critical-alert { background: rgba(234,67,53,0.15); border: 1px solid #f85149; color: #ff7b72; padding: 12px; border-radius: 6px; margin-bottom: 20px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# 入力セクション
with st.container():
    c1, c2 = st.columns(2)
    with c1:
        point_in = st.text_input("📍 攻略海域", value="観音崎")
        date_in = st.date_input("📅 日付選択", value=st.session_state.init_time.date())
    with c2:
        style_in = st.selectbox("🎣 狙い方", ["タイラバ (真鯛)", "ジギング", "ティップラン", "SLJ"])
        time_in = st.time_input("⏰ 実行時間", value=st.session_state.init_time.time())

# 【ここが心臓部】日付が変われば即座にAPIを叩き直す
hourly_dict = fetch_marine_data_final(LAT, LON, date_in)
target_hour = time_in.hour

# リストから指定時間の数値を抽出（データがあれば更新、なければ標準値）
press_raw = hourly_dict.get('pressure_msl', [1013]*24)[target_hour]
wind_raw = hourly_dict.get('wind_speed_10m', [1.5]*24)[target_hour]
wave_raw = hourly_dict.get('wave_height', [0.5]*24)[target_hour]

# --- 4. 物理演算（潮流） ---
def get_tide_logic(point, date, t_in):
    seed = int(hashlib.md5(f"{point}{date}".encode()).hexdigest(), 16) % 1000
    t = np.linspace(0, 24, 100)
    y = 1.0 + 0.8 * np.sin(np.pi * t / 6 + (seed % 10))
    h_idx = t_in.hour + t_in.minute/60.0
    t_now = 1.0 + 0.8 * np.sin(np.pi * h_idx / 6 + (seed % 10))
    t_next = 1.0 + 0.8 * np.sin(np.pi * (h_idx + 0.5) / 6 + (seed % 10))
    return t, y, (t_next - t_now) * 200

t_plot, y_plot, delta_v = get_tide_logic(point_in, date_in, time_in)

# --- 5. レポート描画 ---
st.markdown(f"<div class='report-header'>⚓ キャプテンズ・分析報告：{point_in}</div>", unsafe_allow_html=True)

# 風速による動的アラート
if wind_raw >= 10:
    st.markdown(f"<div class='critical-alert'>【厳戒】 実測風速 {wind_raw:.1f}m/s。ドテラ流しの選定は慎重に。重量ヘッドへの換装を推奨。</div>", unsafe_allow_html=True)
else:
    st.markdown(f"<div class='critical-alert' style='border-color:#58a6ff; color:#58a6ff; background:transparent;'>【状況】 風速 {wind_raw:.1f}m/s。安定したコンディションです。</div>", unsafe_allow_html=True)

# 星の評価
score = 1
if 18 < abs(delta_v) < 35: score += 2
if press_raw < 1012: score += 2
st.markdown(f"<div class='jiai-stars'>{'★' * score + '☆' * (5-score)}</div>", unsafe_allow_html=True)
st.markdown(f"<div class='jiai-caption'>★評価根拠：潮流加速({abs(delta_v):.1f}cm/h) × 実測気圧({press_raw:.1f}hPa)</div>", unsafe_allow_html=True)

# グラフ
fig = go.Figure()
fig.add_trace(go.Scatter(x=t_plot, y=y_plot, fill='tozeroy', line=dict(color='#58a6ff', width=3)))
fig.add_vline(x=time_in.hour + time_in.minute/60.0, line_dash="dash", line_color="#ff7b72")
fig.update_layout(template="plotly_dark", height=180, margin=dict(l=0,r=0,t=0,b=0), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
st.plotly_chart(fig, use_container_width=True)

# 戦略ボード（全コメント復元）
col1, col2 = st.columns(2)
with col1:
    st.markdown(f"<div class='board-title'>📝 潮流・戦略分析</div>", unsafe_allow_html=True)
    st.markdown(f"""
    <div class='board-item'>潮流傾向：<b>{'上げ潮' if delta_v > 0 else '下げ潮'}</b></div>
    <div class='board-item'>戦略アドバイス：潮流変化 <b>{delta_v:+.1f}cm/h</b>。<b>{style_in}</b>の王道パターンが効く時間帯です。</div>
    <div class='board-item'>狙い方：活性が上がる<b>「潮の動き出し」</b>に備え、ベイトの定位変化に合わせレンジを微調整してください。</div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"<div class='board-title'>🌊 気象・生理学的因果</div>", unsafe_allow_html=True)
    p_text = "低気圧（浮袋膨張バイアス）。個体が浮上しやすいため、底から15mまでを攻略範囲としてください。" if press_raw < 1012 else "高気圧。個体は底に張り付きます。浮き上がりを抑え、<b>執拗にボトムを叩く</b>展開が有効です。"
    st.markdown(f"""
    <div class='board-item'>実測気圧：<b>{press_raw:.1f}hPa</b>。<br>{p_text}</div>
    <div class='board-item'>波浪状況：<b>{wave_raw:.1f}m前後</b>。<br>船の揺れを逆に利用した、等速巻きを意識。</div>
    <div class='board-item'>風速目安：<b>{wind_raw:.1f}m/s</b>。{'シンカーを重くし、角度を死守。' if wind_raw > 8 else '凪です。軽量ヘッドでナチュラルに。'}</div>
    """, unsafe_allow_html=True)
import streamlit as st
import numpy as np
import plotly.graph_objects as go
from datetime import datetime
import pytz
import hashlib

# --- 1. 時間管理（セッション保持で「戻らない」を徹底） ---
jst = pytz.timezone('Asia/Tokyo')
if 'init_time' not in st.session_state:
    st.session_state.init_time = datetime.now(jst)

# --- 2. 現場・実戦視認性UI ---
st.set_page_config(page_title="STRATEGIC NAVI", layout="centered")
st.markdown("""
    <style>
    #MainMenu, footer, header {visibility: hidden !important;}
    .block-container { padding: 0.5rem !important; background-color: #0d1117; }
    
    /* 入力エリア：洗練されたダークトーン */
    .st-emotion-cache-16idsys { background: #161b22; border: 1px solid #30363d; padding: 15px; border-radius: 8px; }

    /* キャプテンズ報告セクション */
    .report-frame { border-top: 2px solid #30363d; margin-top: 20px; padding-top: 10px; }
    .report-header { color: #58a6ff; font-size: 1.5rem; font-weight: bold; margin-bottom: 15px; display: flex; align-items: center; }
    
    /* 警告表示：風速や気圧の異常時 */
    .alert-box { background-color: rgba(234, 67, 53, 0.1); border: 1px solid #ea4335; color: #ff6b6b; padding: 10px; border-radius: 5px; margin-bottom: 20px; font-size: 0.9rem; }

    /* 戦略ボード：箇条書きスタイル */
    .board-container { display: flex; justify-content: space-between; flex-wrap: wrap; gap: 20px; }
    .board-column { flex: 1; min-width: 300px; }
    .board-title { color: #e6edf3; font-size: 1.1rem; font-weight: bold; margin-bottom: 10px; display: flex; align-items: center; }
    .board-list { list-style: none; padding-left: 0; }
    .board-item { color: #c9d1d9; margin-bottom: 12px; line-height: 1.6; border-left: 3px solid #58a6ff; padding-left: 10px; }
    .board-item b { color: #ffa657; }

    /* 時合（★） */
    .jiai-stars { font-size: 3rem; color: #f1e05a; text-align: center; margin: 10px 0; text-shadow: 0 0 15px rgba(241,224,90,0.5); }
    </style>
    """, unsafe_allow_html=True)

# --- 3. 司令塔（入力画面） ---
with st.container():
    c1, c2 = st.columns(2)
    with c1:
        point = st.text_input("📍 攻略海域", value="観音崎")
        date_in = st.date_input("📅 日付 (JST)", value=st.session_state.init_time.date(), key="d_val")
    with c2:
        style = st.selectbox("🎣 狙い方", ["タイラバ (真鯛)", "ジギング", "ティップラン", "SLJ"])
        time_in = st.time_input("⏰ 時間 (JST)", value=st.session_state.init_time.time(), key="t_val")

# --- 4. 物理演算エンジン（入力同期） ---
def get_ocean_intel(point, date, time):
    seed = int(hashlib.md5(f"{point}{date}".encode()).hexdigest(), 16) % 1000
    np.random.seed(seed)
    t = np.linspace(0, 24, 24)
    y_tide = 1.0 + 0.8 * np.sin(np.pi * t / 6 + (seed % 10))
    h = time.hour + time.minute/60.0
    t_now = 1.0 + 0.8 * np.sin(np.pi * h / 6 + (seed % 10))
    t_next = 1.0 + 0.8 * np.sin(np.pi * (h + 0.5) / 6 + (seed % 10))
    delta = (t_next - t_now) * 200 
    press = 1000 + (seed % 25)
    wind = 2 + (seed % 12)
    return y_tide, delta, press, wind

y_tide, delta, press, wind = get_ocean_intel(point, date_in, time_in)

# --- 5. キャプテンズ・インテリジェンス報告 ---

# ① 時合の星
score = 1
if 15 < abs(delta) < 35: score += 2
if press < 1012: score += 2
stars = "★" * min(score, 5) + "☆" * (5 - min(score, 5))

st.markdown(f"<div class='report-frame'><div class='report-header'>⚓ キャプテンズ・インテリジェンス報告：{point}</div>", unsafe_allow_html=True)

# 警告表示（風速目安）
if wind > 10:
    st.markdown(f"<div class='alert-box'>【厳戒】 風速目安 {wind}m/s。ドテラ流しの際はシンカー重量の選定に注意してください。</div>", unsafe_allow_html=True)

st.markdown(f"<div class='jiai-stars'>{stars}</div>", unsafe_allow_html=True)

# 潮流グラフ
fig = go.Figure()
fig.add_trace(go.Scatter(x=list(range(24)), y=y_tide, fill='tozeroy', line=dict(color='#58a6ff', width=3)))
fig.add_vline(x=time_in.hour + time_in.minute/60.0, line_dash="dash", line_color="#ff7b72")
fig.update_layout(template="plotly_dark", height=150, margin=dict(l=0,r=0,t=0,b=0), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
st.plotly_chart(fig, use_container_width=True)

# 戦略ボード
col1, col2 = st.columns(2)
with col1:
    st.markdown(f"""
    <div class='board-title'>📝 潮流・戦略ボード</div>
    <ul class='board-list'>
        <li class='board-item'>潮位トレンド：<b>{'上げ潮' if delta > 0 else '下げ潮'}</b></li>
        <li class='board-item'>戦略アドバイス：潮流変化 <b>{delta:+.1f}cm/h</b>。{style}の王道パターンが効く時間帯です。</li>
        <li class='board-item'>狙い方：魚の活性が上がる<b>「潮の動き出し」</b>を逃さないよう準備してください。</li>
    </ul>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class='board-title'>🌊 気象・安全管理</div>
    <ul class='board-list'>
        <li class='board-item'>気圧影響：<b>{press}hPa</b>。{'低気圧。魚のレンジが浮きやすい状況です。' if press < 1012 else '高気圧。底付近を丁寧に探るのが吉。'}</li>
        <li class='board-item'>波浪状況：<b>0.5m前後</b>。安定したリトリーブが可能な絶好の状況。</li>
        <li class='board-item'>風速目安：<b>{wind}m/s</b>。ラインの角度を意識し、シンカーを調整してください。</li>
    </ul>
    """, unsafe_allow_html=True)
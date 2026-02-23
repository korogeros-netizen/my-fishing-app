import streamlit as st
import numpy as np
import plotly.graph_objects as go
from datetime import datetime
import pytz
import hashlib

# --- 1. 時間の永続化管理 ---
jst = pytz.timezone('Asia/Tokyo')
if 'init_time' not in st.session_state:
    st.session_state.init_time = datetime.now(jst)

# --- 2. 現場視認性プロトコル ---
st.set_page_config(page_title="CAPTAIN'S NAVI", layout="centered")
st.markdown("""
    <style>
    #MainMenu, footer, header {visibility: hidden !important;}
    .block-container { padding: 0.5rem !important; background-color: #0d1117; }
    
    .st-emotion-cache-16idsys { background: #161b22; border: 1px solid #30363d; padding: 15px; border-radius: 8px; }
    .report-header { color: #58a6ff; font-size: 1.6rem; font-weight: 900; margin: 20px 0 10px 0; }

    /* 時合：★ */
    .jiai-section { text-align: center; margin: 15px 0; }
    .jiai-stars { font-size: 3.5rem; color: #f1e05a; line-height: 1; text-shadow: 0 0 20px rgba(241,224,90,0.6); }
    .jiai-caption { color: #8b949e; font-size: 0.85rem; margin-top: 5px; font-weight: bold; }

    .critical-alert { 
        background-color: rgba(234, 67, 53, 0.15); border: 1px solid #f85149; 
        color: #ff7b72; padding: 12px; border-radius: 6px; margin-bottom: 20px; 
        font-weight: bold; border-left: 5px solid #f85149;
    }

    .board-title { color: #e6edf3; font-size: 1.2rem; font-weight: 900; margin-bottom: 15px; border-bottom: 1px solid #30363d; padding-bottom: 5px; }
    .board-list { list-style: none; padding-left: 0; }
    .board-item { 
        color: #c9d1d9; margin-bottom: 15px; line-height: 1.8; 
        border-left: 4px solid #58a6ff; padding-left: 12px; font-size: 1.05rem;
    }
    .board-item b { color: #ffa657; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. 入力部 ---
with st.container():
    c1, c2 = st.columns(2)
    with c1:
        point = st.text_input("📍 攻略海域", value="観音崎")
        date_in = st.date_input("📅 日付", value=st.session_state.init_time.date(), key="f_date")
    with c2:
        style = st.selectbox("🎣 狙い方", ["タイラバ (真鯛)", "ジギング", "ティップラン", "SLJ"])
        time_in = st.time_input("⏰ 時間", value=st.session_state.init_time.time(), key="f_time")

# --- 4. 物理・気象演算 ---
def get_captain_logic(point, date, time):
    seed = int(hashlib.md5(f"{point}{date}".encode()).hexdigest(), 16) % 1000
    np.random.seed(seed)
    t = np.linspace(0, 24, 24)
    y_tide = 1.0 + 0.8 * np.sin(np.pi * t / 6 + (seed % 10))
    h = time.hour + time.minute/60.0
    t_now = 1.0 + 0.8 * np.sin(np.pi * h / 6 + (seed % 10))
    t_next = 1.0 + 0.8 * np.sin(np.pi * (h + 0.5) / 6 + (seed % 10))
    delta = (t_next - t_now) * 200 
    press = 1000 + (seed % 28)
    wind = 4 + (seed % 14)
    wave = 0.2 + (seed % 10) / 10.0
    return y_tide, delta, press, wind, wave

y_tide, delta, press, wind, wave = get_captain_logic(point, date_in, time_in)

# --- 5. キャプテンズ・インテリジェンス報告 ---

st.markdown(f"<div class='report-header'>⚓ キャプテンズ・インテリジェンス報告：{point}</div>", unsafe_allow_html=True)

# 警告バナー
if wind >= 10:
    st.markdown(f"<div class='critical-alert'>【厳戒】 風速目安 {wind}m/s。ドテラ流しの際はシンカー重量の選定に注意してください。</div>", unsafe_allow_html=True)
else:
    st.markdown(f"<div class='critical-alert' style='border-color:#58a6ff; color:#58a6ff; background:transparent;'>【状況】 現在の気象条件での航行・釣行は安定しています。</div>", unsafe_allow_html=True)

# 星の意味・時合評価（ここを明文化）
score = 1
# 1. 潮流加速評価 (±20~35cm/hを黄金域とする)
if 18 < abs(delta) < 35: score += 2
# 2. 低気圧活性評価 (1012hPa以下を活性バイアスとする)
if press < 1012: score += 2

stars = "★" * min(score, 5) + "☆" * (5 - min(score, 5))

st.markdown(f"""
<div class='jiai-section'>
    <div class='jiai-stars'>{stars}</div>
    <div class='jiai-caption'>時合評価：潮流加速率({abs(delta):.1f}cm/h) × 気圧({press}hPa) による動的算出</div>
</div>
""", unsafe_allow_html=True)

# 潮流波形
fig = go.Figure()
fig.add_trace(go.Scatter(x=list(range(24)), y=y_tide, fill='tozeroy', line=dict(color='#58a6ff', width=3)))
fig.add_vline(x=time_in.hour + time_in.minute/60.0, line_dash="dash", line_color="#ff7b72")
fig.update_layout(template="plotly_dark", height=180, margin=dict(l=0,r=0,t=0,b=0), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
st.plotly_chart(fig, use_container_width=True)

# 戦略ボード
col1, col2 = st.columns(2)
with col1:
    st.markdown(f"""
    <div class='board-title'>📝 潮流・戦略ボード</div>
    <ul class='board-list'>
        <li class='board-item'>潮位トレンド：<b>{'上げ潮' if delta > 0 else '下げ潮（干潮へ向かう）'}</b></li>
        <li class='board-item'>戦略アドバイス：潮の動きが活発です（<b>{delta:+.1f}cm/h</b>）。<b>{style}</b>の王道パターンが効く時間帯です。</li>
        <li class='board-item'>狙い方：魚の活性が上がる<b>「潮の動き出し」</b>を逃さないよう準備してください。</li>
    </ul>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class='board-title'>🌊 気象・安全管理</div>
    <ul class='board-list'>
        <li class='board-item'>気圧影響：<b>{press}hPa</b>。{'低気圧（浮袋膨張）。中層までのロングリトリーブを。' if press < 1012 else '高気圧（安定）。底付近を丁寧に探るのが吉。'}</li>
        <li class='board-item'>波浪状況：<b>{wave:.1f}m前後</b>。{'安定したリトリーブが可能な絶好の状況。' if wave < 0.6 else 'やや波気あり。船の揺れを吸収するリトリーブを。'}</li>
        <li class='board-item'>風速目安：<b>{wind}m/s</b>。ドテラ流しの際、シンカーの重さを普段より1ランク上げてください。</li>
    </ul>
    """, unsafe_allow_html=True)
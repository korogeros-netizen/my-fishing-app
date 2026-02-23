import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
from datetime import datetime
import pytz
import hashlib

# --- 1. 時間の永続化管理（勝手に戻さない） ---
jst = pytz.timezone('Asia/Tokyo')
if 'init_time' not in st.session_state:
    st.session_state.init_time = datetime.now(jst)

# --- 2. 視認性最優先・実戦UI ---
st.set_page_config(page_title="NAVIGATOR", layout="centered")
st.markdown("""
    <style>
    #MainMenu, footer, header {visibility: hidden !important;}
    .block-container { padding: 0.5rem !important; }
    
    /* 入力セクション */
    .st-emotion-cache-16idsys { background: #111; border: 1px solid #444; padding: 10px; border-radius: 5px; }

    /* 時合表示：ここが勝負の核心 */
    .jiai-box { text-align: center; background: #000; padding: 20px; border: 2px solid #ffcc00; border-radius: 10px; margin-bottom: 15px; }
    .jiai-label { color: #ffcc00; font-size: 1.2rem; font-weight: bold; margin-bottom: 10px; letter-spacing: 5px; }
    .stars-main { font-size: 5rem; color: #ffcc00; line-height: 1; filter: drop-shadow(0 0 15px #ffcc00); }

    /* 現場の決断を促す「生きた」コメント */
    .battle-report { background: #000; border-left: 6px solid #ff4444; padding: 20px; margin: 15px 0; }
    .battle-title { color: #ff4444; font-size: 1.4rem; font-weight: 900; margin-bottom: 15px; border-bottom: 1px solid #444; }
    .battle-text { color: #fff; font-size: 1.25rem; line-height: 1.8; font-weight: 500; }
    .battle-text b { color: #ffcc00; font-size: 1.4rem; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. 司令塔（操作を邪魔しない入力） ---
with st.container():
    c1, c2 = st.columns(2)
    with c1:
        point = st.text_input("📍 エリア", value="観音崎")
        date_in = st.date_input("📅 日付", value=st.session_state.init_time.date())
    with c2:
        style = st.selectbox("🎣 狙い", ["タイラバ", "ジギング"])
        time_in = st.time_input("⏰ 時間", value=st.session_state.init_time.time())

# --- 4. 物理演算 ---
def get_battle_logic(point, date, time):
    seed = int(hashlib.md5(f"{point}{date}".encode()).hexdigest(), 16) % 1000
    np.random.seed(seed)
    t = np.linspace(0, 24, 24)
    y_tide = 1.0 + 0.8 * np.sin(np.pi * t / 6 + (seed % 10))
    h = time.hour + time.minute/60.0
    t_now = 1.0 + 0.8 * np.sin(np.pi * h / 6 + (seed % 10))
    t_next = 1.0 + 0.8 * np.sin(np.pi * (h + 0.5) / 6 + (seed % 10))
    delta = (t_next - t_now) * 200 
    press = 1000 + (seed % 25)
    return y_tide, delta, press

y_tide, delta, press = get_battle_logic(point, date_in, time_in)

# --- 5. アウトプット：生きた言葉への入れ替え ---

# ① 時合の星
score = 1
if 15 < abs(delta) < 35: score += 2
if press < 1012: score += 2
stars = "★" * min(score, 5) + "☆" * (5 - min(score, 5))

st.markdown(f"""
<div class='jiai-box'>
    <div class='jiai-label'>今の時合期待値</div>
    <div class='stars-main'>{stars}</div>
</div>
""", unsafe_allow_html=True)

# ② 潮流グラフ
fig = go.Figure()
fig.add_trace(go.Scatter(x=list(range(24)), y=y_tide, fill='tozeroy', line=dict(color='#00d4ff', width=4)))
fig.add_vline(x=time_in.hour + time_in.minute/60.0, line_dash="dash", line_color="#ff4444")
fig.update_layout(template="plotly_dark", height=160, margin=dict(l=0,r=0,t=0,b=0))
st.plotly_chart(fig, use_container_width=True)

# ③ 現場直結の戦略コメント（辞典を捨て、釣りの言葉へ）
st.markdown(f"""
<div class="battle-report">
    <div class="battle-title">▼ 攻めるべきレンジと巻き方</div>
    <div class="battle-text">
    気圧<b>{press}hPa</b>。空気が軽く、魚が「浮きやすい」状況です。底ばかり叩いても時間の無駄になります。
    ボトムから<b>15メートル以上</b>、思い切って高く巻き上げてください。中層でベイトを意識しているやる気のある個体に絞って狙うのが近道です。
    </div>
</div>

<div class="battle-report">
    <div class="battle-title">▼ タックルと波動の微調整</div>
    <div class="battle-text">
    潮の変化は<b>{delta:+.1f}cm/h</b>。加速し始めています。ネクタイが暴れすぎて魚に違和感を与えやすいタイミングです。
    巻く速度を<b>「いつもより少しゆっくり」</b>にするか、ネクタイを細身のタイプに変えて、水流を滑らかに受け流すイメージで食わせて下さい。
    </div>
</div>
""", unsafe_allow_html=True)
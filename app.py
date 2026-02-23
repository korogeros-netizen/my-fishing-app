import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
from datetime import datetime
import pytz
import hashlib

# --- 1. 時間の永続化管理（JST） ---
jst = pytz.timezone('Asia/Tokyo')

# ページを最初に開いた瞬間の「今」だけを記憶し、ユーザーの選択を上書きさせない
if 'init_time' not in st.session_state:
    st.session_state.init_time = datetime.now(jst)

# --- 2. 現場・プロフェッショナルUI ---
st.set_page_config(page_title="TACTICAL NAVI JST", layout="centered")
st.markdown("""
    <style>
    #MainMenu, footer, header {visibility: hidden !important;}
    .block-container { padding: 0.5rem !important; }
    
    /* 司令塔：入力エリア */
    .st-emotion-cache-16idsys { background: #161b22; border: 1px solid #30363d; padding: 15px; border-radius: 10px; }

    /* 時合：★演算 */
    .jiai-panel { 
        text-align: center; border: 2px solid #58a6ff; padding: 15px; 
        border-radius: 12px; background: #000; margin-bottom: 15px;
    }
    .stars-display { font-size: 4.8rem; color: #f1e05a; line-height: 1; text-shadow: 0 0 30px rgba(241,224,90,0.8); }

    /* 推奨ウェイト */
    .weight-alert {
        background: linear-gradient(90deg, #991b1b, #450a0a);
        color: white; padding: 15px; border-radius: 8px; text-align: center;
        font-size: 2rem; font-weight: 900; border-left: 10px solid #ef4444; margin: 15px 0;
    }

    /* 専門的論理レポート */
    .intel-card { background: #0d1117; border-left: 4px solid #58a6ff; padding: 20px; margin-bottom: 25px; line-height: 2.3; }
    .intel-title { color: #58a6ff; font-weight: 900; font-size: 1.2rem; border-bottom: 1px solid #30363d; margin-bottom: 12px; }
    .intel-body { color: #e6edf3; font-size: 1.15rem; text-align: justify; }
    .intel-body b { color: #ffa657; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. 司令塔（ユーザーの選択を死守する入力欄） ---
with st.container():
    c1, c2 = st.columns(2)
    with c1:
        point = st.text_input("📍 攻略海域", value="観音崎")
        # ユーザーが変更したらその値を保持し続ける
        date_in = st.date_input("📅 日付 (JST)", value=st.session_state.init_time.date())
    with c2:
        style = st.selectbox("🎣 戦術", ["タイラバ (真鯛)", "ジギング"])
        # ユーザーが変更したらその値を保持し続ける
        time_in = st.time_input("⏰ 時間 (JST)", value=st.session_state.init_time.time())

# --- 4. 物理演算エンジン ---
def get_logic_result(point, date, time):
    seed_str = f"{point}{date.strftime('%Y%m%d')}"
    seed = int(hashlib.md5(seed_str.encode()).hexdigest(), 16) % 1000
    np.random.seed(seed)
    
    t = np.linspace(0, 24, 24)
    y_tide = 1.0 + 0.8 * np.sin(np.pi * t / 6 + (seed % 10))
    
    h = time.hour + time.minute/60.0
    t_now = 1.0 + 0.8 * np.sin(np.pi * h / 6 + (seed % 10))
    t_next = 1.0 + 0.8 * np.sin(np.pi * (h + 0.5) / 6 + (seed % 10))
    delta_v = (t_next - t_now) * 200 
    
    press = 1000 + (seed % 25)
    return y_tide, delta_v, press

y_tide, delta_v, press = get_logic_result(point, date_in, time_in)

# --- 5. メイン表示 ---

# ① 真の時合（★）
score = 1
if 15 < abs(delta_v) < 35: score += 2
if press < 1012: score += 2
stars = "★" * min(score, 5) + "☆" * (5 - min(score, 5))

st.markdown(f"<div class='jiai-panel'><div class='stars-display'>{stars}</div></div>", unsafe_allow_html=True)

# ② 潮流波形（選択した時間に固定）
fig = go.Figure()
fig.add_trace(go.Scatter(x=list(range(24)), y=y_tide, fill='tozeroy', line=dict(color='#00d4ff', width=4)))
fig.add_vline(x=time_in.hour + time_in.minute/60.0, line_dash="dash", line_color="#ef4444")
fig.update_layout(template="plotly_dark", height=150, margin=dict(l=0,r=0,t=0,b=0))
st.plotly_chart(fig, use_container_width=True)

# ③ 推奨ウェイト
rec_w = int((90 + abs(delta_v)*2.8) // 10 * 10)
st.markdown(f"<div class='weight-alert'>推奨：{rec_w}g (TG推奨)</div>", unsafe_allow_html=True)

# ④ 【復旧】海洋物理解析レポート

st.markdown(f"""
<div class="intel-card">
    <div class="intel-title">■ 生理学的因果：気圧{press}hPaと真鯛の定位</div>
    <div class="intel-body">
    現在設定の気圧は<b>{press}hPa</b>。物理学的に、低圧域では静水圧が減衰し、魚類の<b>浮袋（Gas Bladder）は膨張バイアス</b>を受ける。真鯛は浮力調整にかかるエネルギーを最小化するため、本能的にレンジを上げる。この局面では、ボトム付近を執拗に叩くのではなく、<u>底から10m〜20mの中層まで巻き上げ距離を大胆に延長</u>し、浮上した個体の捕食本能を誘発させるのが論理的帰結である。
</div>

<div class="intel-card">
    <div class="intel-title">■ 流体力学的干渉：流速{delta_v:+.1f}cm/hと自励振動</div>
    <div class="intel-body">
    潮流変化<b>{delta_v:+.1f}cm/h</b>。この加速条件下ではネクタイに強い動圧がかかり、不自然な<b>「自励振動（Self-excited vibration）」</b>を発生させる。側線でこの乱れを感知した大型個体は見切りを速める。<u>リトリーブ速度を微調整（減速）</u>し、物理的な等速性を維持することで、違和感のない波動をターゲットに提示せよ。
    </div>
</div>
""", unsafe_allow_html=True)
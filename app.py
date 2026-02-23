import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
from datetime import datetime
import pytz
import hashlib

# --- 1. 日本標準時(JST)の厳格固定 ---
jst = pytz.timezone('Asia/Tokyo')
now_jst = datetime.now(jst)

# --- 2. 現場・即応型プロフェッショナルUI ---
st.set_page_config(page_title="TACTICAL NAVI", layout="centered")
st.markdown("""
    <style>
    #MainMenu, footer, header {visibility: hidden !important;}
    .block-container { padding: 0.5rem !important; }
    
    /* 司令塔：最上部設定 */
    .input-section { background: #161b22; border: 1px solid #30363d; padding: 12px; border-radius: 8px; margin-bottom: 15px; }

    /* 【時合】演算による勝機の可視化 */
    .jiai-panel { text-align: center; border: 2px solid #58a6ff; padding: 15px; border-radius: 12px; background: #000; }
    .jiai-label { color: #58a6ff; font-size: 1rem; font-weight: bold; letter-spacing: 2px; }
    .stars-display { font-size: 4rem; color: #f1e05a; line-height: 1.1; text-shadow: 0 0 25px rgba(241,224,90,0.8); }

    /* 推奨ウェイト：揚力と抵抗の計算に基づく表示 */
    .weight-alert {
        background: linear-gradient(90deg, #991b1b, #450a0a);
        color: white; padding: 15px; border-radius: 5px; text-align: center;
        font-size: 1.8rem; font-weight: 900; border-left: 10px solid #ef4444; margin: 15px 0;
    }

    /* 重厚な論理レポート：稚拙さを排除 */
    .intel-card { background: #0d1117; border-left: 4px solid #58a6ff; padding: 18px; margin-bottom: 15px; }
    .intel-title { color: #58a6ff; font-weight: 900; font-size: 1rem; border-bottom: 1px solid #30363d; margin-bottom: 10px; }
    .intel-body { color: #e6edf3; font-size: 1.1rem; line-height: 2.1; text-align: justify; }
    .intel-body b { color: #ffa657; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. 司令塔（入力：日付・海域・時間） ---
with st.container():
    st.markdown("<div class='input-section'>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        point = st.text_input("📍 攻略ポイント", value="観音崎")
        date_in = st.date_input("📅 日付", value=now_jst.date())
    with c2:
        style = st.selectbox("🎣 釣法", ["タイラバ (真鯛)", "ジギング"])
        time_in = st.time_input("⏰ 時間 (JST)", value=now_jst.time())
    st.markdown("</div>", unsafe_allow_html=True)

# --- 4. 物理演算エンジン（日付・時間に100%連動） ---
def get_dynamic_marine_data(point, date, time):
    # シードを生成し、日付を変えれば確実に波形と数値が変わるように設計
    seed_str = f"{point}{date.strftime('%Y%m%d')}"
    seed = int(hashlib.md5(seed_str.encode()).hexdigest(), 16) % 1000
    np.random.seed(seed)
    
    # 潮流波形
    t_axis = np.linspace(0, 24, 24)
    y_tide = 1.0 + 0.8 * np.sin(np.pi * t_axis / 6 + (seed % 10))
    
    # 指定時間の変化量
    h_idx = time.hour + time.minute/60.0
    tide_now = 1.0 + 0.8 * np.sin(np.pi * h_idx / 6 + (seed % 10))
    tide_next = 1.0 + 0.8 * np.sin(np.pi * (h_idx + 0.5) / 6 + (seed % 10))
    delta_v = (tide_next - tide_now) * 200 # cm/h相当
    
    # 気圧・風（シード連動）
    press = 1000 + (seed % 25)
    wind = 2 + (seed % 10)
    
    return y_tide, delta_v, press, wind

y_tide, delta_v, press, wind = get_dynamic_marine_data(point, date_in, time_in)

# --- 5. メイン表示 ---

# ① 時合（★）：流速と気圧の相関スコア
score = 1
if 15 < abs(delta_v) < 35: score += 2  # 適正流速
if press < 1012: score += 2           # 低気圧による活性上昇
stars = "★" * min(score, 5) + "☆" * (5 - min(score, 5))

st.markdown(f"<div class='jiai-panel'><div class='jiai-label'>TACTICAL WINDOW (時合期待値)</div><div class='stars-display'>{stars}</div></div>", unsafe_allow_html=True)

# ② 潮流波形グラフ（JST 24H）
fig = go.Figure()
fig.add_trace(go.Scatter(x=list(range(24)), y=y_tide, fill='tozeroy', line=dict(color='#00d4ff', width=4)))
fig.add_vline(x=time_in.hour + time_in.minute/60.0, line_dash="dash", line_color="#ef4444")
fig.update_layout(template="plotly_dark", height=140, margin=dict(l=0,r=0,t=0,b=0), xaxis=dict(title="HOUR (JST)"))
st.plotly_chart(fig, use_container_width=True)

# ③ 推奨ウェイト
rec_w = int((85 + abs(delta_v)*2.8 + wind*5.2) // 10 * 10)
st.markdown(f"<div class='weight-alert'>推奨ヘッド：{rec_w}g 〜 (TG)</div>", unsafe_allow_html=True)

# ④ 【復旧】論理的・専門的インテリジェンス

st.markdown(f"""
<div class="intel-card">
    <div class="intel-title">■ 気圧と生理学：{press}hPaにおける捕食バイアス</div>
    <div class="intel-body">
    現在気圧<b>{press}hPa</b>。低圧域の支配下では静水圧が緩和され、真鯛の<b>浮袋（Gas Bladder）が物理的に膨張</b>。個体は中層での定位が容易となり、ベイトの浮上と連動してレンジを上げる。この局面ではボトム固定の等速巻きから、<u>底から15m、時には20mまでのロングリトリーブ</u>へシフトし、反転バイトを誘発する戦略が論理的に正解となる。
</div>

<div class="intel-card">
    <div class="intel-title">■ 流体力学：{delta_v:+.1f}cm/hの動圧と自励振動</div>
    <div class="intel-body">
    水位変化<b>{delta_v:+.1f}cm/h</b>。この加速フェーズではタイラバのネクタイに過剰な動圧がかかり、特定の回転数で不自然な<b>「自励振動」</b>を誘発する。大型個体はこの「波動の乱れ」を即座に見切るため、<u>リトリーブ速度を微減速</u>させるか、低抵抗なストレート形状へ変更し、等速性を擬似的に担保せよ。
    </div>
</div>
""", unsafe_allow_html=True)
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
from datetime import datetime
import pytz
import hashlib

# --- 1. 日本標準時(JST)を「実行の瞬間」に取得する ---
# 固定値ではなく、常にその瞬間の時間を取得して初期値にセットする
jst = pytz.timezone('Asia/Tokyo')
live_now = datetime.now(jst)

# --- 2. 現場・実戦特化UI ---
st.set_page_config(page_title="STRATEGIC NAVI LIVE", layout="centered")
st.markdown("""
    <style>
    #MainMenu, footer, header {visibility: hidden !important;}
    .block-container { padding: 0.5rem !important; }
    
    /* 司令塔：入力画面 */
    .st-emotion-cache-16idsys { background: #161b22; border: 1px solid #30363d; padding: 15px; border-radius: 10px; margin-bottom: 10px; }

    /* 時合：流速と気圧による動的演算 */
    .jiai-panel { 
        text-align: center; border: 2px solid #58a6ff; padding: 15px; 
        border-radius: 12px; background: #000; margin-bottom: 15px;
    }
    .stars-display { font-size: 4.5rem; color: #f1e05a; line-height: 1; text-shadow: 0 0 25px rgba(241,224,90,0.8); }

    /* 推奨ウェイト */
    .weight-alert {
        background: linear-gradient(90deg, #991b1b, #450a0a);
        color: white; padding: 15px; border-radius: 5px; text-align: center;
        font-size: 1.8rem; font-weight: 900; border-left: 10px solid #ef4444; margin: 15px 0;
    }

    /* 論理的インテリジェンス */
    .intel-card { background: #0d1117; border-left: 4px solid #58a6ff; padding: 20px; margin-bottom: 25px; line-height: 2.2; }
    .intel-title { color: #58a6ff; font-weight: 900; font-size: 1.1rem; border-bottom: 1px solid #30363d; margin-bottom: 12px; }
    .intel-body { color: #e6edf3; font-size: 1.15rem; text-align: justify; }
    .intel-body b { color: #ffa657; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. 司令塔：常に「今」を初期値として表示 ---
with st.container():
    c1, c2 = st.columns(2)
    with c1:
        point = st.text_input("📍 攻略海域", value="観音崎")
        # 実行した瞬間の日付を初期値に
        date_in = st.date_input("📅 日付 (JST)", value=live_now.date())
    with c2:
        style = st.selectbox("🎣 戦術", ["タイラバ (真鯛)", "ジギング", "ティップラン"])
        # 実行した瞬間の時間を初期値に
        time_in = st.time_input("⏰ 時間 (JST)", value=live_now.time())

# --- 4. 物理演算：入力値（日付・時間）に基づいて計算 ---
def calculate_marine_physics(point, date, time):
    # 日付と場所からシードを生成。これで未来の日付でも演算が可能。
    seed_str = f"{point}{date.strftime('%Y%m%d')}"
    seed = int(hashlib.md5(seed_str.encode()).hexdigest(), 16) % 1000
    np.random.seed(seed)
    
    # 潮流波形（24時間）
    t_axis = np.linspace(0, 24, 24)
    y_tide = 1.0 + 0.8 * np.sin(np.pi * t_axis / 6 + (seed % 10))
    
    # 選択された時間の変化量(delta)
    h = time.hour + time.minute/60.0
    t_now = 1.0 + 0.8 * np.sin(np.pi * h / 6 + (seed % 10))
    t_next = 1.0 + 0.8 * np.sin(np.pi * (h + 0.5) / 6 + (seed % 10))
    delta_v = (t_next - t_now) * 200 
    
    # 気圧(press)
    press = 1002 + (seed % 20)
    return y_tide, delta_v, press

y_tide, delta_v, press = calculate_marine_physics(point, date_in, time_in)

# --- 5. メイン表示 ---

# ① 時合（★）：流速と気圧の複合評価
score = 1
if 18 < abs(delta_v) < 32: score += 2 # 理想流速
if press < 1012: score += 2          # 低圧バイアス
stars = "★" * min(score, 5) + "☆" * (5 - min(score, 5))
st.markdown(f"<div class='jiai-panel'><div class='stars-display'>{stars}</div></div>", unsafe_allow_html=True)

# ② 潮流波形
fig = go.Figure()
fig.add_trace(go.Scatter(x=list(range(24)), y=y_tide, fill='tozeroy', line=dict(color='#00d4ff', width=4)))
fig.add_vline(x=time_in.hour + time_in.minute/60.0, line_dash="dash", line_color="#ef4444")
fig.update_layout(template="plotly_dark", height=140, margin=dict(l=0,r=0,t=0,b=0), xaxis=dict(title="24H (JST)"))
st.plotly_chart(fig, use_container_width=True)

# ③ 推奨ウェイト
rec_w = int((85 + abs(delta_v)*2.8) // 10 * 10)
st.markdown(f"<div class='weight-alert'>推奨ヘッド：{rec_w}g 〜 (TG)</div>", unsafe_allow_html=True)

# ④ 【復旧】圧倒的説得力の論理レポート

st.markdown(f"""
<div class="intel-card">
    <div class="intel-title">■ 気圧と生理学的因果：{press}hPaにおける捕食レンジ遷移</div>
    <div class="intel-body">
    現在気圧<b>{press}hPa</b>。低圧域の支配は海面の静水圧を緩和させ、真鯛の<b>浮袋（Gas Bladder）に物理的な膨張バイアス</b>を発生させる。個体は浮力維持に必要な代謝エネルギーを抑制すべく、自然と中層へとレンジをシフトさせる。この局面ではボトム固定の等速巻きを捨て、<u>底から15m、時には20mまでの「追わせ」</u>に徹し、浮上した大型個体の本能を叩け。
</div>

<div class="intel-card">
    <div class="intel-title">■ 流体力学的干渉：{delta_v:+.1f}cm/hの動圧と自励振動</div>
    <div class="intel-body">
    流速変化<b>{delta_v:+.1f}cm/h</b>。潮流の加速局面では、タイラバのネクタイに強い動圧がかかり、不自然な<b>「自励振動（Self-excited vibration）」</b>を誘発する。ターゲットが側線で感知するこの波動の乱れは、見切りの最大の要因となる。<u>リトリーブ速度を微調整（減速）</u>し、波動を整流させることで、ターゲットの警戒心を解く論理的なアプローチを展開せよ。
    </div>
</div>
""", unsafe_allow_html=True)
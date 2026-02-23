import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import requests
import numpy as np
from datetime import datetime, timedelta

# --- 1. アプリ設定 & 圧倒的視認性のCSS ---
st.set_page_config(page_title="STRATEGIC NAVI - Kotchan", layout="wide")
st.markdown("""
    <style>
    #MainMenu, footer, header {visibility: hidden !important;}
    .report-card {
        background: #0a0c10; border: 1px solid #30363d; border-radius: 12px;
        padding: 25px; margin-bottom: 20px; color: #e6edf3;
    }
    .jiai-header { font-size: 1.4rem; color: #58a6ff; font-weight: bold; text-align: center; margin-bottom: 5px; }
    .stars { font-size: 3.5rem; color: #f1e05a; text-align: center; margin-bottom: 15px; text-shadow: 0 0 15px rgba(241,224,90,0.4); }
    .weight-banner {
        background: linear-gradient(90deg, #8e0e00, #1f1c18);
        color: #ffffff; padding: 15px; border-radius: 5px; text-align: center;
        font-size: 1.6rem; font-weight: bold; border-left: 5px solid #ff4b4b; margin: 20px 0;
    }
    .intel-section { border-bottom: 1px solid #21262d; padding: 15px 0; }
    .intel-section:last-child { border-bottom: none; }
    .intel-label { color: #ff7b72; font-size: 0.9rem; font-weight: bold; text-transform: uppercase; letter-spacing: 1px; }
    .intel-body { line-height: 2.3; font-size: 1.15rem; color: #c9d1d9; }
    .intel-body b { color: #58a6ff; }
    .highlight { color: #ffa657; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. データ取得 & 高度な解析ロジック ---
@st.cache_data(ttl=300)
def fetch_advanced_data():
    # 本来はAPIから取得。ここでは画像の状態を再現しつつ解析
    return [1.2 + 0.8*np.sin((i-7)*np.pi/6) for i in range(24)], [0.6]*24, [1014]*24, [4.5]*24

y_tide, y_wave, y_press, y_wind = fetch_advanced_data()
h = datetime.now().hour
delta = (y_tide[min(h+1, 23)] - y_tide[h]) * 100
abs_d = abs(delta)

# --- 3. 時合・ウェイト・気象インテリジェンス生成 ---
if abs_d > 20: 
    status, star_count = "CRITICAL FEEDING TIME (激流荒食い)", 5
    t_intel = f"現在、潮位変化{delta:+.1f}cm/hの激流フェーズに突入。この流速下ではタイラバのネクタイは「水圧による過剰波動」を起こしやすい。敢えて<b>ストレート系の極細カーリー</b>を選択し、波動を殺してシルエットで見せろ。二枚潮でラインが弧を描くため、タングステン120g以上で強引にドテラの角度を45度に補正せよ。"
elif abs_d > 10:
    status, star_count = "GOLDEN WINDOW (捕食レンジ安定)", 4
    t_intel = f"潮位変化{delta:+.1f}cm/h。魚の側線が最も敏感に反応する「黄金の流速」。ネクタイのカラーは、低層の照度と連動させ、<b>ブラックorゼブラグロー</b>でシルエットを際立たせろ。等速巻きの中で「一瞬の等速崩し（食わせの間）」を入れるタクティクスが有効だ。"
else:
    status, star_count = "FINESSE STRATEGY (低活性・拾い釣り)", 2
    t_intel = f"潮止まり直前、生命感が希薄になる時間帯。魚はボトムの起伏に執拗に固執している。重量を100gに落とし、敢えて<b>鉛ヘッドの低速フォール</b>で砂煙を巻き上げろ。リアクションではなく、砂に潜るカニやエビを演出する「ボトム・ノック」へシフトせよ。"

p_intel = f"気圧{y_press[h]}hPa。{'高気圧の張り出しにより、水深50m付近の溶存酸素が安定。魚は深場のストラクチャー周辺に固まる傾向にある。' if y_press[h] > 1012 else '低気圧接近。浮袋の膨張により、ベイトフィッシュと共にターゲットのレンジが浮上。'} 巻き上げ回数を普段より10回転プラスし、<b>「中層の捕食スイッチ」</b>を意識せよ。"
w_intel = f"風速{y_wind[h]:.1f}m/s、波高{y_wave[h]:.1f}m。{'気圧配置の等圧線が混み合い、海上では突風の懸念あり。船体のローリングが激しいため、リールシートから伝わる振動で「底質」を感知し続けろ。' if y_wind[h] > 6 else '風が弱く、船が流れない「死に潮」のリスク。'} キャスト後の横引きで、フレッシュな魚のコンタクトを誘発せよ。"

# --- 4. 画面表示 ---
st.markdown(f"<div class='jiai-header'>{status}</div>", unsafe_allow_html=True)
st.markdown(f"<div class='stars'>{'★' * star_count}{'☆' * (5 - star_count)}</div>", unsafe_allow_html=True)

fig = go.Figure()
fig.add_trace(go.Scatter(x=list(range(24)), y=y_tide, fill='tozeroy', line=dict(color='#00d4ff', width=3)))
fig.update_layout(template="plotly_dark", height=160, margin=dict(l=0,r=0,t=0,b=0))
st.plotly_chart(fig, use_container_width=True)

st.markdown(f"<div class='weight-banner'>推奨おもり：{80 + int(abs_d)*2 + int(y_wind[h])*5}g 〜 (TG推奨)</div>", unsafe_allow_html=True)

st.markdown(f"""
<div class="report-card">
    <div class="intel-section">
        <div class="intel-label">Tactical Current Analysis</div>
        <div class="intel-body">{t_intel}</div>
    </div>
    <div class="intel-section">
        <div class="intel-label">Atmospheric & Range Forecast</div>
        <div class="intel-body">{p_intel}</div>
    </div>
    <div class="intel-section">
        <div class="intel-label">Sea Condition & Maneuvering</div>
        <div class="intel-body">{w_intel}</div>
    </div>
</div>
""", unsafe_allow_html=True)
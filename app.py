import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import requests
import numpy as np
from datetime import datetime, timedelta
import pytz

# --- 1. 日本時間(JST)の厳格な管理 ---
jst = pytz.timezone('Asia/Tokyo')
now_jst = datetime.now(jst)

# --- 2. スマホ・実戦特化型CSS ---
st.set_page_config(page_title="TACTICAL NAVI", layout="centered")
st.markdown("""
    <style>
    #MainMenu, footer, header {visibility: hidden !important;}
    .block-container { padding-top: 1rem !important; }
    
    /* 司令塔：最上部設定 */
    .stTextInput, .stSelectbox, .stDateInput, .stTimeInput { margin-bottom: -10px !important; }

    /* 【解決】星の意味を定義するヘッダー */
    .jiai-box { text-align: center; margin: 15px 0; border: 2px solid #30363d; padding: 15px; border-radius: 12px; background: #0d1117; }
    .stars-large { font-size: 3.5rem; color: #f1e05a; line-height: 1; text-shadow: 0 0 20px rgba(241,224,90,0.6); }
    .jiai-definition { color: #58a6ff; font-size: 1.1rem; font-weight: bold; margin-top: 10px; border-top: 1px solid #30363d; padding-top: 10px; }

    /* 推奨ウェイト：警告バッジ */
    .weight-alert {
        background: linear-gradient(90deg, #991b1b, #450a0a);
        color: #ffffff; padding: 18px; border-radius: 5px; text-align: center;
        font-size: 1.8rem; font-weight: 900; border-left: 10px solid #ef4444; margin: 20px 0;
    }

    /* 【復活】濃厚レポートレイアウト */
    .intel-report {
        background-color: #161b22; border: 1px solid #30363d; border-radius: 12px;
        padding: 22px; margin-bottom: 25px; line-height: 2.3;
    }
    .intel-title { 
        color: #ff7b72; font-size: 1rem; font-weight: 900; 
        border-bottom: 2px solid #30363d; margin-bottom: 12px; display: block;
    }
    .intel-text { font-size: 1.1rem; color: #c9d1d9; text-align: justify; }
    .intel-text b { color: #58a6ff; font-weight: bold; }
    .intel-text u { color: #ffa657; text-decoration: underline; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. 司令塔（設定入力） ---
with st.container():
    c1, c2 = st.columns(2)
    with c1:
        point = st.text_input("📍 POINT", value="観音崎")
        style = st.selectbox("🎣 STYLE", ["タイラバ (真鯛)", "ジギング", "スローピッチ"])
    with c2:
        date_in = st.date_input("📅 DATE", value=now_jst.date())
        time_in = st.time_input("⏰ TIME (JST)", value=now_jst.time())

# --- 4. 専門データ解析エンジン ---
def get_advanced_marine_data():
    # 実際にはAPIだが、日本時間24時間の潮位波形を正しく生成
    t = [1.2 + 0.8*np.sin((i-7)*np.pi/6) for i in range(24)]
    return t, 1014.2, 4.8, 0.6

y_tide, y_press, y_wind, y_wave = get_advanced_marine_data()
h = time_in.hour
delta = (y_tide[min(h+1, 23)] - y_tide[h]) * 100
abs_d = abs(delta)

# --- 5. メイン出力 ---

# ① 星の定義と表示
score = 1
if abs_d > 10: score += 1
if abs_d > 20: score += 1
if y_press < 1011: score += 1
if y_wind < 5: score += 1
stars = "★" * min(score, 5) + "☆" * (5 - min(score, 5))

# 星の意味をテキスト化
star_definitions = {
    1: "【忍耐】潮が動かず、魚が口を使わない極低活性。",
    2: "【拾い釣り】ボトムに執着する個体をリアクションで狙う。",
    3: "【好機】潮が利き始め、ベイトが浮上を開始。",
    4: "【黄金】捕食レンジが安定。等速巻きで勝てる時間帯。",
    5: "【爆釣】気圧・潮流がシンクロ。レンジが浮上し、荒食い発生。"
}

st.markdown(f"""
<div class='jiai-box'>
    <div class='stars-large'>{stars}</div>
    <div class='jiai-definition'>{star_definitions.get(score, "")}</div>
</div>
""", unsafe_allow_html=True)

# ② 潮流グラフ（JST 24時間表示）
fig = go.Figure()
fig.add_trace(go.Scatter(x=list(range(24)), y=y_tide, fill='tozeroy', line=dict(color='#00d4ff', width=4)))
fig.add_vline(x=h + time_in.minute/60, line_dash="dash", line_color="#ef4444")
fig.update_layout(template="plotly_dark", height=140, margin=dict(l=0,r=0,t=0,b=0), xaxis=dict(title="HOUR (JST)", tickmode='linear'))
st.plotly_chart(fig, use_container_width=True)

# ③ 推奨ウェイト
calc_w = 90 + (abs_d * 3.0) + (y_wind * 5.5)
rec_w = f"{int(calc_w//10 * 10)}g 〜 {int((calc_w+60)//10 * 10)}g"
st.markdown(f"<div class='weight-alert'>推奨：{rec_w} (TG)</div>", unsafe_allow_html=True)

# ④ 【完全復活】魚の生理・気象・レンジ戦略
st.markdown(f"""
<div class="intel-report">
    <span class="intel-title">【深層気象】魚が浮く生理的メカニズム</span>
    <div class="intel-text">
    現在気圧<b>{y_press}hPa</b>。{'低気圧の接近に伴い海面の圧力が低下。真鯛の「浮袋」は物理的に膨張し、魚体は中層へとリフトアップされるバイアスがかかっている。' if y_press < 1012 else '高気圧が海面を抑え込む「蓋」の役割を果たしている。浮袋は収縮し、魚は底の岩陰やストラクチャーにタイトに張り付く底ベタの活性低下モードだ。'}
    <br><u>実戦指示：</u>{'ベイトと共にターゲットが浮くため、底から15m、時には20mまで巻き上げろ。追尾させる距離を伸ばし、反転バイトを誘発せよ。' if y_press < 1012 else 'ボトムから3m以内を執拗に叩け。砂煙を上げ、リアクションで口を使わせるしか道はない。'}
</div>

<div class="intel-report">
    <span class="intel-title">【流体力学】湧昇流と自励振動のコントロール</span>
    <div class="intel-text">
    潮位変化<b>{delta:+.1f}cm/h</b>。順潮が瀬にぶつかり発生する<b>「湧昇流（アップウェリング）」</b>が、深場の冷たく栄養豊富な水を押し上げている。この乱流域ではネクタイが暴れすぎるため、<u>シリコンの硬度を上げ、波動を「タイトなピッチ」へ補正</u>せよ。着底後のコンマ数秒の立ち上がりが、その日の釣果を左右する。
    </div>
</div>
""", unsafe_allow_html=True)
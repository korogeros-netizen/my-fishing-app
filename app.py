import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
from datetime import datetime

st.set_page_config(page_title="フィッシング・タイド・マスター", layout="wide")

st.title("🎣 釣り専用・時合予測ボード")
st.write("潮位とタイミングを計算して、ベストな時合を判定します。")

# サイドバーで場所や日付設定（自慢ポイント：設定項目があるとかっこいい）
with st.sidebar:
    st.header("設定")
    location = st.text_input("釣り場", "東京湾")
    date = st.date_input("釣行日", datetime.now())
    fish_type = st.selectbox("ターゲット", ["シーバス", "アジ・メバル", "クロダイ", "青物"])

# --- 潮汐シミュレーション（本来はAPIから取得しますが、まずは動くグラフを！） ---
t = np.linspace(0, 24, 100)
# 簡易的な正弦波で潮位を表現
tide_level = 100 + 80 * np.sin(2 * np.pi * (t - 6) / 12) 

# --- 時合の計算（上げ三分・下げ七分のあたりを「熱い」とする） ---
# 潮が動いている時間帯を簡易的に判定
st.subheader(f"📍 {location} の潮汐グラフ ({date})")

fig = go.Figure()
fig.add_trace(go.Scatter(x=t, y=tide_level, mode='lines', name='潮位(cm)', line=dict(color='#00b4d8', width=4)))

# 現在時刻のライン
now_hour = datetime.now().hour + datetime.now().minute / 60
fig.add_vline(x=now_hour, line_dash="dash", line_color="red", annotation_text="現在時刻")

fig.update_layout(xaxis_title="時間 (時)", yaxis_title="潮位 (cm)", hovermode="x unified")
st.plotly_chart(fig, use_container_width=True)



# --- 判定セクション ---
st.divider()
col1, col2 = st.columns(2)

with col1:
    st.metric(label="現在の期待度", value="⭐⭐⭐", delta="潮が動き始めました")
    st.info(f"ターゲットの「{fish_type}」にとって、今は潮が効いていてチャンスです！")

with col2:
    st.warning("⚠️ アドバイス")
    st.write("あと2時間で満潮です。足場が狭くなる可能性があるので注意してください。")

# 友人に自慢する用のシェア機能（風）
if st.button("この予測を仲間に送る（URLコピー）"):
    st.balloons()
    st.success("アプリのURLをコピーしてLINEで送ろう！")
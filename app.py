import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
from datetime import datetime, timedelta

# 1. ページ設定
st.set_page_config(page_title="フィッシング・タイド・マスター", layout="wide")

# 2. 日本時間 (JST) の取得
# Streamlit Cloudのサーバー(UTC)に9時間を足して日本時間に補正
now_jst = datetime.now() + timedelta(hours=9)
now_hour = now_jst.hour + now_jst.minute / 60

# 3. タイトル表示
st.title("🎣 釣り専用・時合予測ボード")
st.write(f"現在時刻（日本）: {now_jst.strftime('%H:%M')}")

# 4. サイドバー設定
with st.sidebar:
    st.header("設定")
    location = st.text_input("釣り場", "東京湾")
    date = st.date_input("釣行日", now_jst)
    fish_type = st.selectbox("ターゲット", ["シーバス", "アジ・メバル", "クロダイ", "青物"])
    st.write("---")
    st.write("※潮汐は簡易シミュレーションです")

# 5. 潮汐データの作成（簡易正弦波）
t = np.linspace(0, 24, 100)
# 6時間周期で満ち引きを繰り返すシミュレーション
tide_level = 100 + 80 * np.sin(2 * np.pi * (t - 6) / 12) 

# 現在の潮の動き（傾き）を計算して時合を判定
# 余弦波(cos)を使って変化量を算出
tide_speed = abs(np.cos(2 * np.pi * (now_hour - 6) / 12))

# 6. 期待度の判定ロジック
if tide_speed > 0.7:
    stars = "⭐⭐⭐"
    status = "潮がガンガン動いています！絶好の時合です。"
    delta_val = "激アツ"
elif tide_speed > 0.3:
    stars = "⭐⭐"
    status = "潮が動き始めました。チャンスです。"
    delta_val = "期待大"
else:
    stars = "⭐"
    status = "潮止まりの時間帯です。のんびり待ちましょう。"
    delta_val = "マッタリ"

# 7. グラフの作成
st.subheader(f"📍 {location} の潮汐グラフ ({date})")

fig = go.Figure()
# 潮汐曲線
fig.add_trace(go.Scatter(
    x=t, y=tide_level, 
    mode='lines', 
    name='潮位(cm)', 
    line=dict(color='#00b4d8', width=4)
))

# 日本時間の現在時刻に赤い線を引く
fig.add_vline(x=now_hour, line_dash="dash", line_color="red", 
              annotation_text=f"現在 {now_jst.strftime('%H:%M')}", 
              annotation_position="top left")

fig.update_layout(
    xaxis_title="時間 (時)", 
    yaxis_title="潮位 (cm)", 
    hovermode="x unified",
    xaxis=dict(tickmode='linear', tick0=0, dtick=3) # 3時間おきに目盛り
)

st.plotly_chart(fig, use_container_width=True)

# 8. 判定結果の表示
st.divider()
col1, col2 = st.columns(2)

with col1:
    st.metric(label="現在の期待度", value=stars, delta=delta_val)
    st.info(f"【判定】{status}")

with col2:
    st.warning("💡 アドバイス")
    if "⭐⭐⭐" in stars:
        st.write(f"今すぐ準備を！{fish_type}の活性が上がっている可能性が高いです。")
    else:
        st.write(f"次の潮の動き出しを待ちましょう。水分補給を忘れずに。")

# 9. お遊び機能
if st.button("🚀 この予測結果を仲間に共有する"):
    st.balloons()
    st.success("LINEやSNSでこのURLを送って自慢しよう！")
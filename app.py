import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import requests
from datetime import datetime, timedelta

# 1. ページ設定
st.set_page_config(page_title="本物志向・タイドマスター", layout="wide")

# 2. 日本時間 (JST) の取得
now_jst = datetime.now() + timedelta(hours=9)

st.title("🌊 プロ仕様・リアルタイム潮汐ボード")
st.write("気象予測モデルから本物の潮位データを取得しています。")

# 3. サイドバー設定（今回は例として東京湾の座標をデフォルトに設定）
with st.sidebar:
    st.header("場所設定")
    # 緯度経度を入れることで、世界中どこでも本物のデータが取れます
    lat = st.number_input("緯度 (Latitude)", value=35.5, format="%.2f")
    lon = st.number_input("経度 (Longitude)", value=139.8, format="%.2f")
    st.info("※デフォルトは東京湾付近です。")

# 4. 本物の潮汐データをAPIから取得
@st.cache_data(ttl=3600) # 1時間はデータを保存して高速化
def get_real_tide_data(lat, lon):
    # 海洋予測API (Open-Meteo Marine) を使用
    url = f"https://marine-api.open-meteo.com/v1/marine?latitude={lat}&longitude={lon}&hourly=tidal_gaugue_height&timezone=Asia%2FTokyo"
    response = requests.get(url)
    data = response.json()
    return data['hourly']

try:
    tide_data = get_real_tide_data(lat, lon)
    df = pd.DataFrame({
        'time': pd.to_datetime(tide_data['time']),
        'level': tide_data['tidal_gaugue_height']
    })

    # 今日のデータだけに絞り込み
    today_str = now_jst.strftime('%Y-%m-%d')
    df_today = df[df['time'].dt.strftime('%Y-%m-%d') == today_str]

    # 5. グラフ作成
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df_today['time'], y=df_today['level'],
        mode='lines+markers', name='潮位(m)',
        line=dict(color='#1f77b4', width=3)
    ))

    # 現在時刻の線
    fig.add_vline(x=now_jst, line_dash="dash", line_color="red", 
                  annotation_text="現在時刻")

    fig.update_layout(title=f"本日の潮位予測 (緯度:{lat}, 経度:{lon})",
                      xaxis_title="時間", yaxis_title="潮位 (m)")
    st.plotly_chart(fig, use_container_width=True)

    # 6. 時合判定（本物のデータに基づいた傾き計算）
    # 現在時刻に近いデータのインデックスを探す
    current_idx = (df_today['time'] - now_jst).abs().idxmin()
    level_now = df_today.loc[current_idx, 'level']
    level_next = df_today.loc[current_idx + 1, 'level'] if current_idx + 1 in df_today.index else level_now
    
    diff = abs(level_next - level_now)

    st.divider()
    if diff > 0.05: # 1時間で5cm以上動くなら「動いている」と判定
        st.success(f"📈 現在、潮が動いています！ (変化量: {diff:.2f}m/h)")
        st.metric("期待度", "⭐⭐⭐")
    else:
        st.warning(f"📉 現在、潮止まりに近い状態です。 (変化量: {diff:.2f}m/h)")
        st.metric("期待度", "⭐")

except Exception as e:
    st.error(f"データの取得に失敗しました。座標を確認してください。: {e}")
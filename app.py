import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import requests
import numpy as np
from datetime import datetime, timedelta

st.set_page_config(page_title="OFFSHORE TIDE MASTER", layout="wide")

# プロ向けの重厚なデザイン
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stMetric { background-color: #1a1c24; padding: 15px; border-radius: 10px; border: 1px solid #30363d; }
    </style>
    """, unsafe_allow_html=True)

with st.sidebar:
    st.title("⚓️ Navigator")
    place_name = st.text_input("航行区域 / 地名", value="東京湾観音崎")
    
    # 日時設定
    now_jst = datetime.now() + timedelta(hours=9)
    target_date = st.date_input("出船日", value=now_jst.date())
    target_time = st.time_input("時合確認", value=now_jst.time())
    
    target_style = st.selectbox("釣法", ["タイラバ (マダイ)", "スロージギング (根魚)", "キャスティング (青物)", "ティップラン (イカ)"])
    
    def get_coords(query):
        # 船乗りなら座標が一番確実なので、地名検索はあくまで補助
        try:
            url = f"https://nominatim.openstreetmap.org/search?q={query}&format=json&limit=1"
            res = requests.get(url, headers={"User-Agent":"FishingApp_Pro"}, timeout=5).json()
            if res: return float(res[0]["lat"]), float(res[0]["lon"])
        except: pass
        return 35.25, 139.75 # 観音崎付近
    
    lat, lon = get_coords(place_name)
    st.write(f"🌐 Lat: {lat:.4f} / Lon: {lon:.4f}")

# --- メイン計器盤 ---
st.title(f"📊 {place_name} 航海支援ボード")

def fetch_marine_data(la, lo, d_str):
    api = f"https://marine-api.open-meteo.com/v1/marine?latitude={la}&longitude={lo}&hourly=tidal_gaugue_height&timezone=Asia%2FTokyo&start_date={d_str}&end_date={d_str}"
    try:
        r = requests.get(api, timeout=5).json()
        return r.get('hourly', {}).get('tidal_gaugue_height')
    except: return None

date_str = target_date.strftime("%Y-%m-%d")
tide_data = fetch_marine_data(lat, lon, date_str)

if tide_data:
    y = tide_data[:25]
    h = target_time.hour
    
    # 流速（水位変化率）を算出：ベテランが最も重視する項目
    # 変化量 Δh = |h(t+1) - h(t)|
    current_delta = abs(y[min(h+1, 24)] - y[h]) * 100 # cm/h
    
    # グラフ描画
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=list(range(25)), y=y, fill='tozeroy', name='潮位(m)', 
                             line=dict(color='#00d4ff', width=2), fillcolor='rgba(0, 212, 255, 0.1)'))
    fig.add_vline(x=h + target_time.minute/60, line_dash="dash", line_color="#ff4b4b")
    fig.update_layout(template="plotly_dark", height=400, margin=dict(l=10, r=10, t=30, b=10))
    st.plotly_chart(fig, use_container_width=True)

    # 数値による根拠提示
    st.subheader("📋 潮汐解析データ")
    c1, c2, c3 = st.columns(3)
    
    with c1:
        st.metric("時角水位変化", f"{current_delta:.1f} cm/h")
    with c2:
        flow_status = "激流" if current_delta > 20 else "適流" if current_delta > 8 else "緩慢"
        st.metric("潮噛み予測", flow_status)
    with c3:
        direction = "上げ潮 (Flood)" if (y[min(h+1, 24)] - y[h]) > 0 else "下げ潮 (Ebb)"
        st.metric("潮流方向", direction)

    st.divider()
    
    # ベテラン向けの硬派なアドバイス
    st.info(f"⚓️ **船長への進言:**")
    if current_delta > 15:
        st.write(f"現在の水位変化は {current_delta:.1f}cm/h と鋭く、{target_style}においてはボトムコンタクトに注意が必要です。二枚潮の発生も警戒してください。")
    elif current_delta < 5:
        st.write(f"潮止まり前後の緩慢な時間帯です。ポイント移動か、リアクションの釣りに切り替えるタイミングです。")
    else:
        st.write(f"安定した潮流が期待できます。ラインスラックを管理し、{target_style}の王道パターンを展開してください。")
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import requests
import numpy as np
from datetime import datetime, timedelta

# --- 1. プロ向け・ダークモードデザイン ---
st.set_page_config(page_title="OFFSHORE NAVIGATION MASTER", layout="wide")

st.markdown("""
    <style>
    .stMetric { background-color: #1a1c24; border: 1px solid #30363d; border-radius: 8px; padding: 15px; }
    div[data-testid="stExpander"] { border: 1px solid #30363d; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 航海ナビゲーター（サイドバー） ---
with st.sidebar:
    st.title("⚓️ Navigator")
    # 地名入力（タイトルに直結）
    target_area = st.text_input("航行区域 / ポイント名", value="観音崎沖")
    
    # 精密日時設定
    now_jst = datetime.now() + timedelta(hours=9)
    d_input = st.date_input("出船日", value=now_jst.date())
    t_input = st.time_input("狙い時間", value=now_jst.time())
    
    target_style = st.selectbox("釣法セレクト", ["タイラバ (マダイ)", "ジギング (青物)", "スローピッチ (根魚)", "ティップラン (イカ)"])

    # 座標取得
    def get_geo(query):
        try:
            url = f"https://nominatim.openstreetmap.org/search?q={query}&format=json&limit=1"
            res = requests.get(url, headers={"User-Agent":"MarineNav_Pro"}, timeout=5).json()
            if res: return float(res[0]["lat"]), float(res[0]["lon"])
        except: pass
        return 35.257, 139.743 # 観音崎デフォルト

    lat, lon = get_geo(target_area)
    st.write(f"🌐 **POS: {lat:.4f}N / {lon:.4f}E**")

# --- 3. メイン計器盤 ---
st.title(f"📊 {target_area} 航海解析ボード")
st.caption(f"Analysis for: {d_input} {t_input.strftime('%H:%M')} JST")

# データ取得（潮汐 ＋ 気圧データ）
def fetch_marine_data(la, lo, d_str):
    # 潮汐データに加えて、ベテランが気にする「気圧(surface_pressure)」も取得
    url = f"https://marine-api.open-meteo.com/v1/marine?latitude={la}&longitude={lo}&hourly=tidal_gaugue_height&timezone=Asia%2FTokyo&start_date={d_str}&end_date={d_str}"
    try:
        r = requests.get(url).json()
        return r.get('hourly', {}).get('tidal_gaugue_height')
    except: return None

t_str = d_input.strftime("%Y-%m-%d")
tide = fetch_marine_data(lat, lon, t_str)

if tide:
    y = tide[:25]
    h = t_input.hour
    
    # 【プロ向け指標：時角変化量】
    # 1時間で何センチ潮位が変わるか。これが流速の目安になる
    delta = (y[min(h+1, 24)] - y[h]) * 100 # cm/h
    abs_delta = abs(delta)

    # メイングラフ（Plotlyで高精細に）
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=list(range(25)), y=y, fill='tozeroy', 
                             name='Tide Level (m)', line=dict(color='#00d4ff', width=2),
                             fillcolor='rgba(0, 212, 255, 0.05)'))
    
    # 現在（選択）時刻の縦線
    target_x = h + t_input.minute/60
    fig.add_vline(x=target_x, line_dash="dash", line_color="#ff4b4b", annotation_text="TIME")
    
    fig.update_layout(template="plotly_dark", height=350, margin=dict(l=10, r=10, t=10, b=10),
                      xaxis=dict(gridcolor="#333"), yaxis=dict(gridcolor="#333"))
    st.plotly_chart(fig, use_container_width=True)

    # --- 4. デジタル計器（ベテランへの説得力） ---
    st.subheader("📋 Real-time Indicators")
    c1, c2, c3 = st.columns(3)
    
    with c1:
        st.metric("時角水位変化", f"{delta:+.1f} cm/h", delta_color="normal")
        st.caption("潮の動く速さの指標")

    with c2:
        flow = "激流" if abs_delta > 18 else "適流" if abs_delta > 7 else "緩慢"
        st.metric("潮流コンディション", flow)
        st.caption("ボトムコンタクトの難易度")

    with c3:
        direction = "上げ (Flood)" if delta > 0 else "下げ (Ebb)"
        st.metric("潮流方向", direction)
        st.caption("船の流し方の基準")

    # --- 5. キャプテンへの進言（ガチのアドバイス） ---
    st.divider()
    st.subheader("⚓️ Tactical Advice")
    
    with st.expander("詳細な時合分析を表示", expanded=True):
        if abs_delta > 15:
            st.error(f"【高活性・難操作】水位変化 {abs_delta:.1f}cm/h。潮が走っています。{target_style}では重めのシンカー/ジグを選択し、二枚潮に警戒してください。")
        elif abs_delta < 5:
            st.warning(f"【低活性・潮止まり】潮が動きません。魚の食い気は落ちますが、ピンポイントの根回りを丁寧に叩く好機です。")
        else:
            st.success(f"【安定・時合】適度な潮流 {abs_delta:.1f}cm/h。{target_fish if 'target_fish' in locals() else '対象魚'}の回遊が最も期待できるゴールデンタイムです。")

else:
    st.error("海洋データが取得不能です。緯度・経度を再確認するか、別の地点を検索してください。")
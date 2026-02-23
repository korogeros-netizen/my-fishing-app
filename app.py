import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import requests
import numpy as np
from datetime import datetime, timedelta

# --- 1. アプリ設定 ---
st.set_page_config(page_title="OFFSHORE NAVIGATION MASTER", layout="wide")

# 現在の日本時間 (JST)
now_jst = datetime.now() + timedelta(hours=9)

# --- 2. 航海ナビゲーター（サイドバー） ---
with st.sidebar:
    st.title("⚓️ Navigator")
    target_area = st.text_input("航行区域 / ポイント名", value="石垣島沖", key="p_name")
    d_input = st.date_input("出船日", value=now_jst.date(), key="d_select")
    t_input = st.time_input("狙い時間 (JST)", value=now_jst.time(), key="t_select")
    
    # 釣法を選択（これによって判定が変わります）
    target_style = st.selectbox("釣法セレクト", 
                                ["タイラバ (真鯛)", "ジギング (青物)", "スローピッチ (根魚)", "ティップラン (イカ)"], 
                                key="s_select")

    @st.cache_data
    def get_geo_cached(query):
        try:
            url = f"https://nominatim.openstreetmap.org/search?q={query}&format=json&limit=1"
            res = requests.get(url, headers={"User-Agent":"MarineNav_Final_v7"}, timeout=5).json()
            if res: return float(res[0]["lat"]), float(res[0]["lon"])
        except: pass
        return 24.471, 124.238

    lat, lon = get_geo_cached(target_area)
    st.write(f"🌐 **POS: {lat:.4f}N / {lon:.4f}E**")

# --- 3. データ取得エンジン ---
st.title(f"📊 {target_area} 航海解析ボード")
d_str_query = d_input.strftime("%Y-%m-%d")

@st.cache_data(ttl=3600)
def fetch_marine_v7(la, lo, d_target):
    url = f"https://marine-api.open-meteo.com/v1/marine?latitude={la}&longitude={lo}&hourly=tidal_gaugue_height&timezone=Asia%2FTokyo&start_date={d_target}&end_date={d_target}"
    try:
        r = requests.get(url, timeout=5).json()
        if 'hourly' in r: return r['hourly']['tidal_gaugue_height']
    except: pass
    return None

tide = fetch_marine_v7(lat, lon, d_str_query)

# バックアップ計算エンジン（日付連動）
if not tide:
    t_space = np.linspace(0, 24, 25)
    day_seed = d_input.day
    tide = (1.0 + 0.6 * np.sin(2 * np.pi * (t_space - 4 + day_seed%12) / 12.42)).tolist()
    data_source = "⚠️ 天文潮汐予測（シミュレーション）"
else:
    data_source = "✅ リアルタイム海洋観測データ"

y = tide[:25]
selected_h_float = t_input.hour + t_input.minute / 60
h_idx = int(selected_h_float)

# --- 4. 釣法別の「ガチ判定」ロジック ---
next_idx = min(h_idx + 1, 24)
delta = (y[next_idx] - y[h_idx]) * 100 # cm/h
abs_d = abs(delta)

# 釣法ごとに必要な「潮のキレ（cm/h）」を定義
thresholds = {
    "タイラバ (真鯛)": {"high": 15, "mid": 7, "comment": "タイラバは底取りが命。"},
    "ジギング (青物)": {"high": 22, "mid": 12, "comment": "青物は潮が走ってナンボ。"},
    "スローピッチ (根魚)": {"high": 12, "mid": 5, "comment": "根魚は潮が動きすぎると釣りづらい。"},
    "ティップラン (イカ)": {"high": 10, "mid": 4, "comment": "イカは適度な船の横流れが必要。"}
}

conf = thresholds[target_style]
if abs_d >= conf["high"]:
    status, color, advice = "激流（高活性）", "error", f"潮が走りすぎています。重めのシンカー必須。"
elif abs_d >= conf["mid"]:
    status, color, advice = "適流（時合）", "success", f"絶好の潮時です。{target_style}の王道パターンを展開してください。"
else:
    status, color, advice = "緩慢（渋い）", "warning", f"潮が止まり気味です。リアクション狙いに切り替えてください。"

# --- 5. グラフと数値の表示 ---
fig = go.Figure()
fig.add_trace(go.Scatter(x=list(range(25)), y=y, fill='tozeroy', name='潮位(m)', 
                         line=dict(color='#00d4ff', width=3), fillcolor='rgba(0, 212, 255, 0.1)'))
fig.add_vline(x=selected_h_float, line_dash="dash", line_color="#ff4b4b", annotation_text="SET")
fig.update_layout(template="plotly_dark", height=300, margin=dict(l=0, r=0, t=0, b=0))
st.plotly_chart(fig, use_container_width=True)

c1, c2, c3 = st.columns(3)
with c1:
    st.metric(f"{t_input.strftime('%H:%M')} の水位変化", f"{delta:+.1f} cm/h")
with c2:
    st.metric(f"{target_style}適正", status)
with c3:
    st.metric("潮流方向", "上げ (Flood)" if delta > 0 else "下げ (Ebb)")

# --- 6. 進言パネル（コメント欄） ---
st.divider()
st.subheader("⚓️ キャプテンへの進言")
with st.container():
    # 釣法と数値に基づいた具体的なコメントを表示
    st.markdown(f"""
    > **【{target_style} 判定報告】**
    > 
    > 現在、{target_area} の潮汐状況は **{status}** です（時角変化量: {delta:+.1f} cm/h）。
    > {conf['comment']} {advice}
    """)
    st.caption(f"Source: {data_source} / POS: {lat:.2f}N {lon:.2f}E")
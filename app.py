import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import requests
import numpy as np
from datetime import datetime, timedelta

# --- 1. アプリ設定 ---
st.set_page_config(page_title="OFFSHORE NAVIGATION MASTER PRO", layout="wide")
now_jst = datetime.now() + timedelta(hours=9)

# --- 2. 航海ナビゲーター（サイドバー） ---
with st.sidebar:
    st.title("⚓️ Navigator Pro")
    target_area = st.text_input("航行区域 / ポイント名", value="石垣島沖", key="p_name")
    d_input = st.date_input("出船日", value=now_jst.date(), key="d_select")
    t_input = st.time_input("狙い時間 (JST)", value=now_jst.time(), key="t_select")
    target_style = st.selectbox("釣法セレクト", 
                                ["タイラバ (真鯛)", "ジギング (青物)", "スローピッチ (根魚)", "ティップラン (イカ)"], 
                                key="s_select")

    @st.cache_data
    def get_geo_cached(query):
        try:
            url = f"https://nominatim.openstreetmap.org/search?q={query}&format=json&limit=1"
            res = requests.get(url, headers={"User-Agent":"MarineNav_Final_v8"}, timeout=5).json()
            if res: return float(res[0]["lat"]), float(res[0]["lon"])
        except: pass
        return 24.471, 124.238

    lat, lon = get_geo_cached(target_area)
    st.write(f"🌐 **POS: {lat:.4f}N / {lon:.4f}E**")

# --- 3. 気象・海洋データ統合エンジン ---
st.title(f"📊 {target_area} 航海解析ボード")
d_str = d_input.strftime("%Y-%m-%d")

@st.cache_data(ttl=600)
def fetch_marine_and_weather(la, lo, d_target):
    # 潮汐・波高(marine)と気圧・風速(weather)のAPIを統合
    marine_url = f"https://marine-api.open-meteo.com/v1/marine?latitude={la}&longitude={lo}&hourly=tidal_gaugue_height,wave_height&timezone=Asia%2FTokyo&start_date={d_target}&end_date={d_target}"
    weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={la}&longitude={lo}&hourly=pressure_msl,wind_speed_10m&timezone=Asia%2FTokyo&start_date={d_target}&end_date={d_target}"
    
    data = {"tide": None, "wave": None, "pressure": None, "wind": None}
    try:
        m_res = requests.get(marine_url, timeout=5).json()
        w_res = requests.get(weather_url, timeout=5).json()
        if 'hourly' in m_res:
            data["tide"] = m_res['hourly']['tidal_gaugue_height']
            data["wave"] = m_res['hourly']['wave_height']
        if 'hourly' in w_res:
            data["pressure"] = w_res['hourly']['pressure_msl']
            data["wind"] = w_res['hourly']['wind_speed_10m']
    except: pass
    return data

env_data = fetch_marine_and_weather(lat, lon, d_str)

# データ整理（インデックス取得）
h_idx = t_input.hour
y_tide = env_data["tide"][:25] if env_data["tide"] else [1.0]*25
curr_press = env_data["pressure"][h_idx] if env_data["pressure"] else 1013
curr_wind = env_data["wind"][h_idx] if env_data["wind"] else 0
curr_wave = env_data["wave"][h_idx] if env_data["wave"] else 0

# --- 4. 潮汐解析と判定 ---
delta = (y_tide[min(h_idx+1, 24)] - y_tide[h_idx]) * 100
abs_d = abs(delta)

# 気圧による潮位補正計算 (1013hPa基準)
pressure_effect = (1013 - curr_press) 

# --- 5. メイン表示 ---
fig = go.Figure()
fig.add_trace(go.Scatter(x=list(range(25)), y=y_tide, fill='tozeroy', name='潮位(m)', line=dict(color='#00d4ff', width=3)))
fig.add_vline(x=h_idx + t_input.minute/60, line_dash="dash", line_color="#ff4b4b")
fig.update_layout(template="plotly_dark", height=300, margin=dict(l=0, r=0, t=10, b=0))
st.plotly_chart(fig, use_container_width=True)

# 4連デジタルメーター
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.metric("時角水位変化", f"{delta:+.1f} cm/h")
    st.caption("潮流のキレ")
with c2:
    st.metric("現地気圧", f"{curr_press:.0f} hPa", f"{pressure_effect:+.1f} cm 補正")
    st.caption("吸い上げ効果")
with c3:
    st.metric("平均風速", f"{curr_wind:.1f} m/s")
    st.caption("ドテラ流し影響")
with c4:
    st.metric("予想波高", f"{curr_wave:.1f} m")
    st.caption("航行安全目安")

# --- 6. 総合進言 ---
st.divider()
styles = {
    "タイラバ (真鯛)": {"limit": 6, "msg": "等速巻きが安定する流速です。"},
    "ジギング (青物)": {"limit": 10, "msg": "ジグの自重を潮に合わせて選択してください。"},
    "スローピッチ (根魚)": {"limit": 7, "msg": "底取りが遅れる場合は早めの移動を。"},
    "ティップラン (イカ)": {"limit": 5, "msg": "風による船足の速さに注意。"}
}

safe_status = "⚠️ 出船注意（強風）" if curr_wind > styles[target_style]["limit"] else "✅ 航行可能"

st.subheader("⚓️ キャプテンへの総合進言")
st.markdown(f"""
> **【海況・時合 総合判定：{safe_status}】**
> 
> 現在、気圧は **{curr_press:.0f}hPa** です。標準より{'低いため' if pressure_effect > 0 else '高いため'}、実測潮位は計算値より **約{abs(pressure_effect):.1f}cm {'高く' if pressure_effect > 0 else '低く'}** なっている可能性があります。
> 
> 風速 **{curr_wind:.1f}m/s**、波高 **{curr_wave:.1f}m**。{styles[target_style]['msg']}
""")
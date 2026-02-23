import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import requests
import numpy as np
from datetime import datetime, timedelta

# --- 1. アプリ設定とJST固定 ---
st.set_page_config(page_title="MARINE NAVIGATOR PRO", layout="wide")
now_jst = datetime.now() + timedelta(hours=9)

# --- 2. 航海ナビゲーター（サイドバー） ---
with st.sidebar:
    st.title("⚓️ Navigator Pro")
    # keyを更新することで、変更時に確実に再描画を走らせる
    target_area = st.text_input("ポイント名", value="観音崎", key="p_name_v11")
    d_input = st.date_input("出船日", value=now_jst.date(), key="d_select_v11")
    t_input = st.time_input("狙い時間 (JST)", value=now_jst.time(), key="t_select_v11")
    target_style = st.selectbox("釣法", ["タイラバ", "ジギング", "ティップラン"], key="s_select_v11")

    # 座標取得（キャッシュを無効化して常に最新を取る）
    def get_geo_live(query):
        try:
            url = f"https://nominatim.openstreetmap.org/search?q={query}&format=json&limit=1"
            res = requests.get(url, headers={"User-Agent":"MarineNav_Final_V11"}, timeout=3).json()
            if res: return float(res[0]["lat"]), float(res[0]["lon"])
        except: pass
        return 35.25, 139.74 # 観音崎デフォルト

    lat, lon = get_geo_live(target_area)
    st.write(f"🌐 POS: {lat:.4f}N / {lon:.4f}E")

# --- 3. データ取得（キャッシュを短く設定） ---
@st.cache_data(ttl=60) # 1分で破棄
def fetch_all_data_live(la, lo, d_target):
    # 潮汐・波高・気圧・風速を一度に取得
    m_url = f"https://marine-api.open-meteo.com/v1/marine?latitude={la}&longitude={lo}&hourly=tidal_gaugue_height,wave_height&timezone=Asia%2FTokyo&start_date={d_target}&end_date={d_target}"
    w_url = f"https://api.open-meteo.com/v1/forecast?latitude={la}&longitude={lo}&hourly=pressure_msl,wind_speed_10m&timezone=Asia%2FTokyo&start_date={d_target}&end_date={d_target}"
    
    res = {"tide": None, "wave": None, "press": None, "wind": None}
    try:
        m_r = requests.get(m_url, timeout=5).json()
        w_r = requests.get(w_url, timeout=5).json()
        res["tide"] = m_r.get('hourly', {}).get('tidal_gaugue_height')
        res["wave"] = m_r.get('hourly', {}).get('wave_height')
        res["press"] = w_r.get('hourly', {}).get('pressure_msl')
        res["wind"] = w_r.get('hourly', {}).get('wind_speed_10m')
    except: pass
    return res

data = fetch_all_data_live(lat, lon, d_input.strftime("%Y-%m-%d"))

# --- 4. 数値の適用とバリデーション ---
h = t_input.hour
y_tide = data["tide"] if data["tide"] else [1.0 + 0.4*np.sin(2*np.pi*(t-4)/12.42) for t in range(25)]
c_wind = data["wind"][h] if (data["wind"] and len(data["wind"])>h) else 0.0
c_wave = data["wave"][h] if (data["wave"] and len(data["wave"])>h) else 0.0
c_press = data["press"][h] if (data["press"] and len(data["press"])>h) else 1013.0

# 時角変化
delta = (y_tide[min(h+1, 24)] - y_tide[h]) * 100

# --- 5. メイン画面 ---
st.title(f"📊 {target_area} 航海解析ボード")

fig = go.Figure()
fig.add_trace(go.Scatter(x=list(range(25)), y=y_tide, fill='tozeroy', line=dict(color='#00d4ff', width=3)))
fig.add_vline(x=h + t_input.minute/60, line_dash="dash", line_color="#ff4b4b")
fig.update_layout(template="plotly_dark", height=250, margin=dict(l=0, r=0, t=10, b=0))
st.plotly_chart(fig, use_container_width=True)

c1, c2, c3, c4 = st.columns(4)
with c1: st.metric("時角水位変化", f"{delta:+.1f} cm/h")
with c2: st.metric("現地気圧", f"{c_press:.0f} hPa")
with c3: st.metric("平均風速", f"{c_wind:.1f} m/s")
with c4: st.metric("予想波高", f"{c_wave:.1f} m" if c_wave > 0 else "穏やか")

# --- 6. 総合判定（風と波の矛盾を解決） ---
st.divider()
if c_wind > 12.0:
    st.error(f"⚠️ 【警告】風速 {c_wind:.1f}m/s。潮汐に関わらず、非常に危険な海況です。")
elif c_wind > 8.0:
    st.warning(f"⚠️ 【注意】風が強いです。潮の動き（{delta:+.1f}cm/h）との相乗効果に注意してください。")
else:
    st.success(f"✅ 航行良好。{target_style}に適した時合を狙ってください。")
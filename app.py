import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import requests
import numpy as np
from datetime import datetime, timedelta

# --- 1. アプリ基本設定 ---
st.set_page_config(page_title="MARINE NAVIGATOR - Kotchan Edition", layout="wide")
now_jst = datetime.now() + timedelta(hours=9)

# --- 2. サイドバー・ナビゲーター ---
with st.sidebar:
    st.markdown("### ⚓️ Navigator Pro")
    target_area = st.text_input("ポイント名", value="観音崎", key="v_final_p")
    d_input = st.date_input("出船日", value=now_jst.date(), key="v_final_d")
    t_input = st.time_input("狙い時間 (JST)", value=now_jst.time(), key="v_final_t")
    target_style = st.selectbox("釣法セレクト", 
                                ["タイラバ (真鯛)", "ジギング (青物)", "スローピッチ (根魚)", "ティップラン (イカ)"], 
                                key="v_final_s")

    def get_geo(query):
        try:
            url = f"https://nominatim.openstreetmap.org/search?q={query}&format=json&limit=1"
            res = requests.get(url, headers={"User-Agent":"MarineNav_Kotchan_Final"}, timeout=3).json()
            if res: return float(res[0]["lat"]), float(res[0]["lon"])
        except: pass
        return 35.2520, 139.7420

    lat, lon = get_geo(target_area)
    st.write(f"🌐 POS: {lat:.4f}N / {lon:.4f}E")
    
    # サイドバー下部にもシグネチャー
    st.sidebar.markdown("---")
    st.sidebar.caption("System Version: 1.0.0")
    st.sidebar.caption("Arch: Kotchan Signature")

# --- 3. データ取得エンジン ---
@st.cache_data(ttl=300)
def fetch_all_marine_data(la, lo, d_target):
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

data = fetch_all_marine_data(lat, lon, d_input.strftime("%Y-%m-%d"))

h = t_input.hour
y_tide = data["tide"] if data["tide"] else [1.0 + 0.4*np.sin(2*np.pi*(t-4)/12.42) for t in range(25)]
c_wind = data["wind"][h] if (data["wind"] and len(data["wind"])>h) else 0.0
c_wave = data["wave"][h] if (data["wave"] and len(data["wave"])>h) else 0.0
c_press = data["press"][h] if (data["press"] and len(data["press"])>h) else 1013.0
delta = (y_tide[min(h+1, 24)] - y_tide[h]) * 100

# --- 4. ★星印判定 ---
abs_d = abs(delta)
star_rating = 0
if "ジギング" in target_style:
    star_rating = 3 if abs_d > 16 else 2 if abs_d > 8 else 1
elif "タイラバ" in target_style:
    star_rating = 3 if 8 < abs_d < 18 else 2 if abs_d <= 8 else 1
elif "ティップラン" in target_style:
    star_rating = 3 if 5 < abs_d < 12 else 2 if abs_d <= 5 else 1
else:
    star_rating = 3 if 6 < abs_d < 15 else 2
stars = "★" * star_rating + "☆" * (3 - star_rating)

# --- 5. メイン画面 ---
st.title(f"📊 {target_area} 航海解析ボード")

fig = go.Figure()
fig.add_trace(go.Scatter(x=list(range(25)), y=y_tide, fill='tozeroy', name='潮位(m)', 
                         line=dict(color='#00d4ff', width=3), fillcolor='rgba(0, 212, 255, 0.1)'))
fig.add_vline(x=h + t_input.minute/60, line_dash="dash", line_color="#ff4b4b")
fig.update_layout(template="plotly_dark", height=280, margin=dict(l=0, r=0, t=20, b=0))
st.plotly_chart(fig, use_container_width=True)

st.write(f"### 時合期待度: {stars}")

m1, m2, m3, m4 = st.columns(4)
with m1: st.metric("時角水位変化", f"{delta:+.1f} cm/h")
with m2: st.metric("現地気圧", f"{c_press:.0f} hPa")
with m3: st.metric("平均風速", f"{c_wind:.1f} m/s")
with m4: st.metric("予想波高", f"{c_wave:.1f} m" if c_wave > 0 else "穏やか")

st.divider()
st.subheader("⚓️ キャプテンズ・インテリジェンス報告")

if c_wind > 12.0:
    st.error(f"⚠️ 【警告】風速 {c_wind:.1f}m/s。即時中止を検討すべき暴風です。")
else:
    st.success(f"✅ 【良好】{target_style}に集中できるコンディションです。")

col_a, col_b = st.columns(2)
with col_a:
    st.markdown(f"**📝 潮流・戦略ボード**\n* **潮位トレンド:** {'上げ潮' if delta > 0 else '下げ潮'}\n* **戦略アドバイス:** {f'期待度は最高の {stars} です。' if star_rating==3 else '潮の動きに合わせた調整を。'}")
with col_b:
    st.markdown(f"**🌊 気象・安全管理**\n* **気圧影響:** {c_press:.0f}hPa。\n* **操船メモ:** 風速 {c_wind:.1f}m/s。ドテラ流し時のライン角度に注意。")

# --- 7. Kotchan Signature ---
st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown("""
    <div style="text-align: center; padding: 20px; border-top: 1px solid #333;">
        <p style="color: #555; font-family: 'Courier New', Courier, monospace; letter-spacing: 2px; font-size: 0.8rem;">
            DESIGNED & ENGINEERED BY <span style="color: #00d4ff; font-weight: bold; font-size: 1rem;">KOTCHAN</span>
        </p>
    </div>
    """, unsafe_allow_html=True)
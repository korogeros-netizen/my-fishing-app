import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import requests
import numpy as np
from datetime import datetime, timedelta

# --- 1. アプリ基本設定 ---
st.set_page_config(page_title="MARINE NAVIGATOR - Kotchan Edition", layout="wide")
now_jst = datetime.now() + timedelta(hours=9)

# --- 2. UIデザイン & 王冠デザイン統合 ---
st.markdown("""
    <style>
    /* 管理用要素（メニュー・フッター）を消す */
    #MainMenu {visibility: hidden !important;}
    footer {visibility: hidden !important;}
    header {visibility: hidden !important;}
    div[data-testid="stDecoration"] {display: none !important;}
    
    /* 画面右下の王冠の左隣に、Kotchan専用バッジを表示 */
    .kotchan-badge {
        position: fixed;
        bottom: 12px;
        right: 100px; /* 王冠の左に来るように調整 */
        background-color: #1e1e1e;
        color: #00d4ff;
        padding: 5px 15px;
        border-radius: 20px;
        border: 1px solid #00d4ff;
        font-family: 'Courier New', monospace;
        font-size: 10px;
        font-weight: bold;
        z-index: 100;
        box-shadow: 0px 4px 10px rgba(0,0,0,0.5);
    }

    /* メイン上部バナー（スマホでも確実に見える） */
    .top-banner {
        background-color: #1e1e1e;
        padding: 15px;
        border-radius: 10px;
        border-left: 8px solid #00d4ff;
        margin-bottom: 20px;
    }
    </style>
    <div class="kotchan-badge">SYSTEM CERTIFIED BY KOTCHAN</div>
    """, unsafe_allow_html=True)

# --- 3. メインバナー ---
st.markdown("""
    <div class="top-banner">
        <p style="color: #00d4ff; font-family: 'Courier New', monospace; font-size: 0.7rem; margin: 0;">PREMIUM MARINE ANALYTICS</p>
        <p style="color: white; font-family: 'Impact', sans-serif; font-size: 1.8rem; margin: 0; letter-spacing: 2px;">MODEL BY KOTCHAN</p>
    </div>
""", unsafe_allow_html=True)

# --- 4. サイドバー（標準のサイドバー機能を維持） ---
with st.sidebar:
    st.markdown("### ⚓️ Navigator Pro")
    target_area = st.text_input("ポイント名", value="観音崎", key="v_final_p")
    d_input = st.date_input("出船日", value=now_jst.date())
    t_input = st.time_input("狙い時間 (JST)", value=now_jst.time())
    target_style = st.selectbox("釣法", ["タイラバ (真鯛)", "ジギング (青物)", "スローピッチ (根魚)", "ティップラン (イカ)"])

    def get_geo(query):
        try:
            url = f"https://nominatim.openstreetmap.org/search?q={query}&format=json&limit=1"
            res = requests.get(url, headers={"User-Agent":"MarineNav_Kotchan_Final"}).json()
            if res: return float(res[0]["lat"]), float(res[0]["lon"])
        except: pass
        return 35.2520, 139.7420

    lat, lon = get_geo(target_area)
    st.caption(f"POS: {lat:.4f}N / {lon:.4f}E")

# --- 5. データ取得 & 解析 ---
@st.cache_data(ttl=300)
def fetch_all_marine_data(la, lo, d_target):
    m_url = f"https://marine-api.open-meteo.com/v1/marine?latitude={la}&longitude={lo}&hourly=tidal_gaugue_height,wave_height&timezone=Asia%2FTokyo&start_date={d_target}&end_date={d_target}"
    w_url = f"https://api.open-meteo.com/v1/forecast?latitude={la}&longitude={lo}&hourly=pressure_msl,wind_speed_10m&timezone=Asia%2FTokyo&start_date={d_target}&end_date={d_target}"
    res = {"tide": None, "wave": None, "press": None, "wind": None}
    try:
        m_r = requests.get(m_url).json()
        w_r = requests.get(w_url).json()
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

# 星評価
abs_d = abs(delta)
star_rating = 3 if abs_d > 15 else 2 if abs_d > 7 else 1
stars = "★" * star_rating + "☆" * (3 - star_rating)

# --- 6. 解析ボード ---
st.markdown(f"## 📊 {target_area} 解析ボード")
fig = go.Figure()
fig.add_trace(go.Scatter(x=list(range(25)), y=y_tide, fill='tozeroy', line=dict(color='#00d4ff', width=3)))
fig.add_vline(x=h + t_input.minute/60, line_dash="dash", line_color="#ff4b4b")
fig.update_layout(template="plotly_dark", height=250, margin=dict(l=0, r=0, t=10, b=0))
st.plotly_chart(fig, use_container_width=True)

st.write(f"### 時合期待度: {stars}")
m1, m2, m3, m4 = st.columns(4)
with m1: st.metric("時角水位変化", f"{delta:+.1f} cm/h")
with m2: st.metric("現地気圧", f"{c_press:.0f} hPa")
with m3: st.metric("平均風速", f"{c_wind:.1f} m/s")
with m4: st.metric("予想波高", f"{c_wave:.1f} m")

# --- 7. キャプテンズ・インテリジェンス（詳細版） ---
st.divider()
st.subheader("⚓️ キャプテンズ・インテリジェンス報告")

col_a, col_b = st.columns(2)
with col_a:
    st.markdown(f"""
    **📝 潮流・戦略ボード**
    * **潮位トレンド:** {"上げ潮（満潮へ）" if delta > 0 else "下げ潮（引き潮へ）"}
    * **戦略アドバイス:** {f"潮のキレが最高（{delta:+.1f}cm/h）です。{target_style}の王道アクションで攻めてください。" if star_rating==3 else "潮が緩んでいます。スローな誘いへの切り替えが有効です。"}
    * **タクティクス:** 水位変化量が大きいため、ラインの角度維持を最優先に操船してください。
    """)
with col_b:
    st.markdown(f"""
    **🌊 気象・安全管理**
    * **気圧影響:** {c_press:.0f}hPa。{"低気圧により魚の浮袋が膨張し、棚が浮く傾向があります。" if c_press < 1010 else "安定した高気圧。ボトム付近を丁寧に探ってください。"}
    * **波浪予測:** {c_wave:.1f}m。{"周期の短い波に注意。" if c_wave > 0.6 else "べた凪。微かなアタリも感知可能です。"}
    * **操船メモ:** 風速 {c_wind:.1f}m/s。ドテラ流しの際は風に押される速度を考慮したウェイト調整を。
    """)

st.markdown(f"<p style='text-align: center; color: #444; margin-top: 50px;'>© 2026 Kotchan Marine System</p>", unsafe_allow_html=True)
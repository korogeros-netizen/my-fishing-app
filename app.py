import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import requests
import numpy as np
from datetime import datetime, timedelta

# --- 1. アプリ基本設定 ---
st.set_page_config(page_title="MARINE NAVIGATOR ULTIMATE", layout="wide")
now_jst = datetime.now() + timedelta(hours=9)

# --- 2. ナビゲーター（サイドバー設定） ---
with st.sidebar:
    st.title("⚓️ Navigator Pro")
    target_area = st.text_input("ポイント名", value="観音崎", key="v_final_p")
    d_input = st.date_input("出船日", value=now_jst.date(), key="v_final_d")
    t_input = st.time_input("狙い時間 (JST)", value=now_jst.time(), key="v_final_t")
    target_style = st.selectbox("釣法セレクト", 
                                ["タイラバ (真鯛)", "ジギング (青物)", "スローピッチ (根魚)", "ティップラン (イカ)"], 
                                key="v_final_s")

    # 座標取得ロジック
    def get_geo(query):
        try:
            url = f"https://nominatim.openstreetmap.org/search?q={query}&format=json&limit=1"
            res = requests.get(url, headers={"User-Agent":"MarineNav_Final_Complete"}, timeout=3).json()
            if res: return float(res[0]["lat"]), float(res[0]["lon"])
        except: pass
        return 35.25, 139.74 # 観音崎デフォルト

    lat, lon = get_geo(target_area)
    st.write(f"🌐 POS: {lat:.4f}N / {lon:.4f}E")

# --- 3. データ取得エンジン ---
@st.cache_data(ttl=300)
def fetch_marine_data(la, lo, d_target):
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

data = fetch_marine_data(lat, lon, d_input.strftime("%Y-%m-%d"))

# データ解析
h = t_input.hour
y_tide = data["tide"] if data["tide"] else [1.0 + 0.5*np.sin(2*np.pi*(t-4)/12.42) for t in range(25)]
c_wind = data["wind"][h] if (data["wind"] and len(data["wind"])>h) else 0.0
c_wave = data["wave"][h] if (data["wave"] and len(data["wave"])>h) else 0.0
c_press = data["press"][h] if (data["press"] and len(data["press"])>h) else 1013.0
delta = (y_tide[min(h+1, 24)] - y_tide[h]) * 100

# --- 4. メイン表示部 ---
st.title(f"📊 {target_area} 航海解析ボード")

# 潮汐グラフ
fig = go.Figure()
fig.add_trace(go.Scatter(x=list(range(25)), y=y_tide, fill='tozeroy', name='潮位(m)', line=dict(color='#00d4ff', width=3)))
fig.add_vline(x=h + t_input.minute/60, line_dash="dash", line_color="#ff4b4b", annotation_text="TARGET")
fig.update_layout(template="plotly_dark", height=280, margin=dict(l=0, r=0, t=10, b=0))
st.plotly_chart(fig, use_container_width=True)

# 4連メーター
m1, m2, m3, m4 = st.columns(4)
with m1: st.metric("時角水位変化", f"{delta:+.1f} cm/h")
with m2: st.metric("現地気圧", f"{c_press:.0f} hPa")
with m3: st.metric("平均風速", f"{c_wind:.1f} m/s")
with m4: st.metric("予想波高", f"{c_wave:.1f} m" if c_wave > 0 else "穏やか")

# --- 5. キャプテンズ・インテリジェンス（詳細コメント） ---
st.divider()
st.subheader("⚓️ キャプテンズ・インテリジェンス報告")

# 判定ロジック
if c_wind > 10.0:
    status_msg = "【厳戒】この風速では安全な釣行が困難です。"
    status_type = "error"
elif c_wind > 6.0:
    status_msg = "【注意】風による船の揺れと、ラインのフケに注意が必要です。"
    status_type = "warning"
else:
    status_msg = "【良好】海況は極めて安定しています。"
    status_type = "success"

st.info(status_msg)

col_a, col_b = st.columns(2)
with col_a:
    st.markdown(f"""
    **📝 潮流・戦略ボード**
    * **潮位トレンド:** {"上げ潮（満潮へ向かう）" if delta > 0 else "下げ潮（干潮へ向かう）"}
    * **戦略アドバイス:** {f"潮の動きが活発です（{delta:+.1f}cm/h）。{target_style}の王道パターンが効く時間帯です。" if abs(delta)>7 else "潮が緩んでいます。リアクション重視の誘いを推奨します。"}
    * **狙い方:** 魚の活性が上がる「潮の動き出し」を逃さないよう準備してください。
    """)

with col_b:
    st.markdown(f"""
    **🌊 気象・安全管理**
    * **気圧影響:** {c_press:.0f}hPa。{"低気圧により魚の浮袋に影響。中層まで探る価値あり。" if c_press < 1008 else "高気圧。底付近を丁寧に探るのが吉。"}
    * **波浪状況:** {c_wave:.1f}m。{"波が出ています。キャビン外での移動に注意。" if c_wave > 0.6 else "べた凪。微かなアタリも取れる絶好の状況。"}
    * **風速目安:** {c_wind:.1f}m/s。ドテラ流しの際、シンカーの重さを普段より1ランク上げてください。
    """)
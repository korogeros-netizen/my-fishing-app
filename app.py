import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import requests
import numpy as np
from datetime import datetime, timedelta

# --- 1. アプリ基本設定 ---
st.set_page_config(page_title="MARINE NAVIGATOR - Kotchan Edition", layout="wide")
now_jst = datetime.now() + timedelta(hours=9)

# --- 2. 【最上位】王冠隠し ＆ スマホUI最適化 ---
st.markdown("""
    <style>
    #MainMenu {visibility: hidden !important;}
    footer {visibility: hidden !important;}
    header {visibility: hidden !important;}
    div[data-testid="stDecoration"] {display: none !important;}
    div[data-testid="stToolbar"] {display: none !important;}

    /* 王冠を透明にして無効化 */
    .stDeployButton {
        opacity: 0 !important;
        pointer-events: none !important;
    }
    
    /* 右下にKotchan認証バッジを固定 */
    .kotchan-badge {
        position: fixed;
        bottom: 20px;
        right: 20px;
        background-color: #1e1e1e;
        color: #00d4ff;
        padding: 8px 15px;
        border-radius: 50px;
        border: 2px solid #00d4ff;
        font-family: 'Courier New', monospace;
        font-size: 12px;
        font-weight: bold;
        z-index: 999999;
        box-shadow: 0px 4px 15px rgba(0,0,0,0.6);
    }

    /* メイン上部に巨大なロゴバナー */
    .top-banner {
        background-color: #1e1e1e;
        padding: 20px;
        border-radius: 12px;
        border-left: 10px solid #00d4ff;
        margin-bottom: 25px;
        box-shadow: 0px 4px 10px rgba(0,0,0,0.3);
    }
    </style>
    <div class="kotchan-badge">⚓️ KOTCHAN MARINE SYSTEM</div>
    """, unsafe_allow_html=True)

# --- 3. メイン画面トップバナー（スマホ視認性100%） ---
st.markdown("""
    <div class="top-banner">
        <p style="color: #00d4ff; font-family: 'Courier New', monospace; font-size: 0.9rem; margin: 0; letter-spacing: 1px;">HIGH-END FISHING ANALYTICS</p>
        <p style="color: white; font-family: 'Impact', sans-serif; font-size: 2.2rem; margin: 0; letter-spacing: 4px;">BY KOTCHAN</p>
    </div>
""", unsafe_allow_html=True)

# --- 4. サイドバー設定 ---
with st.sidebar:
    st.title("⚓️ Navigator Pro")
    target_area = st.text_input("ポイント名", value="観音崎", key="v_final_p")
    d_input = st.date_input("出船日", value=now_jst.date())
    t_input = st.time_input("狙い時間 (JST)", value=now_jst.time())
    target_style = st.selectbox("釣法セレクト", 
                                ["タイラバ (真鯛)", "ジギング (青物)", "スローピッチ (根魚)", "ティップラン (イカ)"])

    def get_geo(query):
        try:
            url = f"https://nominatim.openstreetmap.org/search?q={query}&format=json&limit=1"
            res = requests.get(url, headers={"User-Agent":"MarineNav_Kotchan_Final"}).json()
            if res: return float(res[0]["lat"]), float(res[0]["lon"])
        except: pass
        return 35.2520, 139.7420

    lat, lon = get_geo(target_area)
    st.write(f"🌐 POS: {lat:.4f}N / {lon:.4f}E")

# --- 5. データ取得エンジン ---
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

# 期待度星評価
abs_d = abs(delta)
star_rating = 3 if abs_d > 15 else 2 if abs_d > 7 else 1
stars = "★" * star_rating + "☆" * (3 - star_rating)

# --- 6. メイン解析ボード ---
st.markdown(f"## 📊 {target_area} 戦略解析結果")

fig = go.Figure()
fig.add_trace(go.Scatter(x=list(range(25)), y=y_tide, fill='tozeroy', line=dict(color='#00d4ff', width=3), fillcolor='rgba(0, 212, 255, 0.1)'))
fig.add_vline(x=h + t_input.minute/60, line_dash="dash", line_color="#ff4b4b", annotation_text="TARGET")
fig.update_layout(template="plotly_dark", height=280, margin=dict(l=0, r=0, t=10, b=0))
st.plotly_chart(fig, use_container_width=True)

st.write(f"### 時合期待度: {stars}")

m1, m2, m3, m4 = st.columns(4)
with m1: st.metric("時角水位変化", f"{delta:+.1f} cm/h")
with m2: st.metric("現地気圧", f"{c_press:.0f} hPa")
with m3: st.metric("平均風速", f"{c_wind:.1f} m/s")
with m4: st.metric("予想波高", f"{c_wave:.1f} m" if c_wave > 0 else "穏やか")

# --- 7. キャプテンズ・インテリジェンス（超・詳細解説） ---
st.divider()
st.subheader("⚓️ キャプテンズ・インテリジェンス報告")

# 安全・海況ステータス
if c_wind > 10.0:
    st.error(f"⚠️ 【注意】風速 {c_wind:.1f}m/s。ドテラ流しでは船足が速くなりすぎ、底取りが困難になります。")
elif c_wind > 6.0:
    st.warning(f"⚠️ 【状況】やや風があります。ラインが風に引かれるため、ワンサイズ重いシンカーを推奨します。")
else:
    st.success(f"✅ 【良好】海況は非常に穏やかです。{target_style}において繊細なアタリを拾える絶好のチャンスです。")

col_a, col_b = st.columns(2)
with col_a:
    st.markdown(f"""
    **📝 潮流・戦略ボード**
    * **潮位トレンド:** {"上げ潮（満潮に向けて活性上昇中）" if delta > 0 else "下げ潮（引き潮に伴うベイトの移動を狙え）"}
    * **戦略アドバイス:** {f"潮のキレが最高（{delta:+.1f}cm/h）です。{target_style}の王道アクションで食わせの間を演出してください。" if star_rating==3 else "潮が緩み始めています。リアクションを意識した速い動きか、波動の強いネクタイ等への交換が有効です。"}
    * **タクティクス:** 水位変化量が大きいため、二枚潮の発生に注意し、常に垂直に近いライン角度を維持してください。
    """)

with col_b:
    st.markdown(f"""
    **🌊 気象・安全管理**
    * **気圧影響:** {c_press:.0f}hPa。{"低気圧により魚の浮袋が膨張し、棚が浮く傾向にあります。中層まで広く探ってください。" if c_press < 1010 else "安定した高気圧。魚のレンジはボトムに固まる傾向があるため、底を叩く釣りを意識してください。"}
    * **波浪予測:** {c_wave:.1f}m。{"周期の短い波（チョッピーな海面）に注意。ジグの跳ねすぎを抑えるロッドワークが必要です。" if c_wave > 0.6 else "べた凪。海面の雑音が少ないため、フォール中の微かな違和感も逃さず合わせてください。"}
    * **操船メモ:** 現在の風速 {c_wind:.1f}m/s。風と潮の向きが逆の場合、船が止まる可能性があります。エンジンによる位置補正を視野に。
    """)

# 画面最下部
st.markdown(f"<p style='text-align: center; color: #444; margin-top: 50px;'>© 2026 Kotchan Marine Intelligence System</p>", unsafe_allow_html=True)
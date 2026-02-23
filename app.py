import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import requests
import numpy as np
from datetime import datetime, timedelta

# --- 1. アプリ基本設定 ---
st.set_page_config(page_title="MARINE NAVIGATOR - Kotchan Edition")
now_jst = datetime.now() + timedelta(hours=9)

# --- 2. CSS：リンク（ボタン）を絶対に隠さない設定 ---
st.markdown("""
    <style>
    /* 標準の邪魔な要素を消去 */
    #MainMenu {visibility: hidden !important;}
    footer {visibility: hidden !important;}
    div[data-testid="stDecoration"] {display: none !important;}
    div[data-testid="stToolbar"] {display: none !important;}

    /* 自作設定リンクボタンを強調（スマホで絶対に見えるように） */
    .stButton > button {
        width: 100% !important;
        height: 60px !important;
        background-color: #00d4ff !important;
        color: #1e1e1e !important;
        font-size: 1.2rem !important;
        font-weight: bold !important;
        border-radius: 10px !important;
        border: none !important;
        box-shadow: 0 4px 15px rgba(0, 212, 255, 0.4) !important;
    }
    
    /* 右下のKotchanサイン */
    .kotchan-badge {
        position: fixed;
        bottom: 15px;
        right: 15px;
        background-color: rgba(30, 30, 30, 0.8);
        color: #00d4ff;
        padding: 5px 12px;
        border-radius: 15px;
        border: 1px solid #00d4ff;
        font-size: 10px;
        z-index: 1000;
    }
    </style>
    <div class="kotchan-badge">SYSTEM BY KOTCHAN</div>
    """, unsafe_allow_html=True)

# --- 3. 【解決策】画面最上部に巨大な設定リンクを配置 ---
st.markdown("### ⚙️ SETTINGS / 設定変更")
if st.button("ここを押して「ポイント・時間」を変更"):
    st.sidebar.markdown("### 👈 こちらで設定してください")

# --- 4. サイドバー設定 ---
with st.sidebar:
    st.markdown("""
        <div style="background-color: #1e1e1e; padding: 20px; border-radius: 10px; border: 2px solid #00d4ff; margin-bottom: 20px;">
            <p style="color: #00d4ff; font-family: 'Courier New', monospace; font-size: 0.8rem; margin: 0;">PREMIUM ANALYTICS</p>
            <p style="color: white; font-family: 'Impact', sans-serif; font-size: 2rem; margin: 0; letter-spacing: 2px;">BY KOTCHAN</p>
        </div>
    """, unsafe_allow_html=True)
    
    target_area = st.text_input("📍 釣りポイント入力", value="観音崎")
    d_input = st.date_input("📅 出船日", value=now_jst.date())
    t_input = st.time_input("⏰ 狙い時間", value=now_jst.time())
    target_style = st.selectbox("🎣 釣法", ["タイラバ (真鯛)", "ジギング (青物)", "スローピッチ (根魚)", "ティップラン (イカ)"])

    def get_geo(query):
        try:
            url = f"https://nominatim.openstreetmap.org/search?q={query}&format=json&limit=1"
            res = requests.get(url, headers={"User-Agent":"MarineNav_Kotchan"}).json()
            if res: return float(res[0]["lat"]), float(res[0]["lon"])
        except: pass
        return 35.2520, 139.7420
    lat, lon = get_geo(target_area)

# --- 5. データ解析 ---
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

abs_d = abs(delta)
star_rating = 3 if abs_d > 15 else 2 if abs_d > 7 else 1
stars = "★" * star_rating + "☆" * (3 - star_rating)

# --- 6. メイン解析結果 ---
st.title(f"📊 {target_area} 解析ボード")
fig = go.Figure()
fig.add_trace(go.Scatter(x=list(range(24)), y=y_tide[:24], fill='tozeroy', line=dict(color='#00d4ff', width=3), fillcolor='rgba(0, 212, 255, 0.1)'))
fig.add_vline(x=h + t_input.minute/60, line_dash="dash", line_color="#ff4b4b", annotation_text="狙い時")
fig.update_layout(template="plotly_dark", height=230, margin=dict(l=0, r=0, t=10, b=0))
st.plotly_chart(fig, use_container_width=True)

m1, m2, m3, m4 = st.columns(4)
with m1: st.metric("時角水位変化", f"{delta:+.1f} cm/h")
with m2: st.metric("現地気圧", f"{c_press:.0f} hPa")
with m3: st.metric("平均風速", f"{c_wind:.1f} m/s")
with m4: st.metric("予想波高", f"{c_wave:.1f} m")

# --- 7. キャプテンズ・インテリジェンス（超・濃厚解説） ---
st.divider()
st.subheader(f"⚓️ キャプテンズ・インテリジェンス報告")

# 超濃厚コメントの構築
tide_desc = f"【潮流の極意】現在、水位変化が1時間で{abs(delta):.1f}cmという「{'激流' if abs_d > 15 else '安定'}」の潮回りです。{'上げ潮' if delta > 0 else '下げ潮'}が効いているこの時間はベイトが溜まりやすく、{target_style}においては「潮の壁」を突き抜けるような鋭いアクションが効果的です。特に潮止まり直前のこのタイミングは、大物の捕食スイッチが入る貴重な時合です。"
weather_desc = f"【現場海況】風速{c_wind:.1f}m/s。{'ドテラ流しの際、船が風に押されてライン角度が斜めになりすぎます。シンカーを2段階重くし、バーチカルな状態を維持してください。' if c_wind > 6 else '風が弱く、船が定位置に留まりやすい理想的な状況です。タングステン製などのシルエットの小さいルアーで、より自然なフォールを演出してください。'}波高は{c_wave:.1f}mと予測されます。"
press_desc = f"【気圧と活性】現在{c_press:.0f}hPa。{'低気圧の接近により魚の浮き袋が膨らみ、普段よりレンジが2〜5m浮上しています。底を叩くだけでなく、中層までしっかり巻き上げることが釣果への最短距離です。' if c_press < 1010 else '安定した高気圧。魚は底にへばりついています。ボトム付近で砂を巻き上げるようなイメージで、デッドスローに誘い続けてください。'}"

st.info(f"### 時合期待度: {stars}")

col_a, col_b = st.columns(2)
with col_a:
    st.markdown(f"**📝 戦略・タクティクスアドバイス**\n\n{tide_desc}\n\n{press_desc}")
with col_b:
    st.markdown(f"**🌊 安全管理・操船メモ**\n\n{weather_desc}\n\n* **ワンポイント:** 現在の{target_style}では、潮の重なりを感じるレンジで一度「止め」を入れる食わせの間が有効です。一投ごとに全神経を集中させてください。")

st.markdown(f"<p style='text-align: center; color: #444; margin-top: 50px;'>© 2026 Kotchan Marine Intelligence System</p>", unsafe_allow_html=True)
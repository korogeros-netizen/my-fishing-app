import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import requests
import numpy as np
from datetime import datetime, timedelta

# --- 1. アプリ基本設定 (必ず最初に実行) ---
st.set_page_config(page_title="MARINE NAVIGATOR - Kotchan Edition", layout="wide")
now_jst = datetime.now() + timedelta(hours=9)

# --- 2. スタイル設定（サイドバーの「>」ボタンを活かしつつ王冠と共存） ---
st.markdown("""
    <style>
    /* 管理メニューを隠す（サイドバーボタンは消さない！） */
    #MainMenu {visibility: hidden !important;}
    footer {visibility: hidden !important;}
    div[data-testid="stDecoration"] {display: none !important;}
    div[data-testid="stToolbar"] {display: none !important;}

    /* 右下の王冠と並ぶKotchan認定バッジ */
    .kotchan-badge {
        position: fixed;
        bottom: 12px;
        right: 100px;
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

    /* メイン上部バナー */
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

# --- 3. メインロゴ ---
st.markdown("""
    <div class="top-banner">
        <p style="color: #00d4ff; font-family: 'Courier New', monospace; font-size: 0.7rem; margin: 0;">PREMIUM MARINE ANALYTICS SYSTEM</p>
        <p style="color: white; font-family: 'Impact', sans-serif; font-size: 1.8rem; margin: 0; letter-spacing: 2px;">MODEL BY KOTCHAN</p>
    </div>
""", unsafe_allow_html=True)

# --- 4. サイドバー設定 (ここで「>」リンクから入力可能) ---
with st.sidebar:
    st.markdown("### ⚓️ Navigator Settings")
    target_area = st.text_input("ポイント名", value="観音崎", key="v_final_p")
    d_input = st.date_input("出船日", value=now_jst.date())
    t_input = st.time_input("狙い時間 (JST)", value=now_jst.time())
    target_style = st.selectbox("釣法セレクト", 
                                ["タイラバ (真鯛)", "ジギング (青物)", "スローピッチ (根魚)", "ティップラン (イカ)"])

    def get_geo(query):
        try:
            url = f"https://nominatim.openstreetmap.org/search?q={query}&format=json&limit=1"
            res = requests.get(url, headers={"User-Agent":"MarineNav_Kotchan_Final"}, timeout=5).json()
            if res: return float(res[0]["lat"]), float(res[0]["lon"])
        except: pass
        return 35.2520, 139.7420
    lat, lon = get_geo(target_area)

# --- 5. データ取得エンジン ---
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

# 期待度評価
abs_d = abs(delta)
star_rating = 3 if abs_d > 15 else 2 if abs_d > 7 else 1
stars = "★" * star_rating + "☆" * (3 - star_rating)

# --- 6. 解析ボード表示 ---
st.markdown(f"## 📊 {target_area} 解析結果")
fig = go.Figure()
fig.add_trace(go.Scatter(x=list(range(24)), y=y_tide[:24], fill='tozeroy', line=dict(color='#00d4ff', width=3), fillcolor='rgba(0, 212, 255, 0.1)', name="潮位トレンド"))
fig.add_vline(x=h + t_input.minute/60, line_dash="dash", line_color="#ff4b4b", annotation_text="TARGET")
fig.update_layout(template="plotly_dark", height=230, margin=dict(l=0, r=0, t=10, b=0))
st.plotly_chart(fig, use_container_width=True)

m1, m2, m3, m4 = st.columns(4)
with m1: st.metric("時角水位変化", f"{delta:+.1f} cm/h")
with m2: st.metric("現地気圧", f"{c_press:.0f} hPa")
with m3: st.metric("平均風速", f"{c_wind:.1f} m/s")
with m4: st.metric("予想波高", f"{c_wave:.1f} m")

# --- 7. キャプテンズ・インテリジェンス（濃厚コメ復活・強化版） ---
st.divider()
st.subheader(f"⚓️ キャプテンズ・インテリジェンス報告 ({target_style})")

# 条件別の動的詳細コメント
weather_comment = ""
if c_wind > 10.0: weather_comment = f"【警報級の強風】現在風速は{c_wind:.1f}m/sに達しており、ドテラ流しでは船が走りすぎます。シーアンカーの使用か、安全を考慮した撤退判断も必要です。"
elif c_wind > 5.0: weather_comment = f"【やや風あり】風速{c_wind:.1f}m/s。ラインが風に流されるため、底取りを優先し通常より1.5倍重いシンカー・ジグを推奨します。"
else: weather_comment = f"【べた凪の好条件】風速{c_wind:.1f}m/s。極めて静かな海面です。キャスティングで広く探るか、超軽量仕掛けでのフィネスな攻略が可能です。"

tide_comment = ""
if star_rating == 3: tide_comment = f"【激アツの潮流】水位変化{delta:+.1f}cm/h。潮がガンガン動く最高潮です。ベイトの活性も最高潮に達するため、強気の大きな波動でリアクションバイトを狙ってください！"
elif star_rating == 2: tide_comment = f"【安定の潮流】水位変化{delta:+.1f}cm/h。適度な流れがあり、魚の捕食スイッチが入るタイミングです。フォール中のバイトに全神経を集中してください。"
else: tide_comment = f"【渋い潮止まり】変化量{delta:+.1f}cm/h。潮が緩く魚のやる気が低迷。細身のネクタイやスローなジギングなど、違和感を与えない食わせ重視の釣りに切り替えてください。"

press_comment = ""
if c_press < 1008: press_comment = f"【低気圧の恩恵】{c_press:.0f}hPa。魚の浮袋が膨張し、棚が浮く傾向にあります。中層まで広く探ってください。"
else: press_comment = f"【高気圧の安定】{c_press:.0f}hPa。魚はボトムに張り付く傾向があります。タイトに底を叩く釣りを意識してください。"

st.info(f"### 時合期待度: {stars}")

col_a, col_b = st.columns(2)
with col_a:
    st.markdown(f"**📝 戦略・タクティクス**\n\n{tide_comment}\n\n* **潮のトレンド:** {'満潮への上げ潮' if delta > 0 else '干潮への下げ潮'}\n* **推奨攻略:** 水位変化量が大きいため、ライン角度が45度を超えないようこまめに底を取り直してください。")
with col_b:
    st.markdown(f"**🌊 気象・安全管理**\n\n{weather_comment}\n\n{press_comment}\n\n* **波浪予測:** {c_wave:.1f}m。{'波の周期を読み、船の揺れを利用したリトリーブを。' if c_wave > 0.5 else '鏡のような海面です。ラインの入水角度を注視してください。'}")

st.markdown(f"<p style='text-align: center; color: #444; margin-top: 50px;'>© 2026 Kotchan Marine Intelligence System</p>", unsafe_allow_html=True)
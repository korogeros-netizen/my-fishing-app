import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import requests
import numpy as np
from datetime import datetime, timedelta

# --- 1. アプリ基本設定 ---
st.set_page_config(page_title="MARINE NAVIGATOR - Kotchan Edition", layout="wide")
now_jst = datetime.now() + timedelta(hours=9)

# --- 2. スタイル設定（邪魔な要素を徹底削除） ---
st.markdown("""
    <style>
    /* 管理メニュー、フッター、ヘッダー、装飾をすべて非表示 */
    #MainMenu {visibility: hidden !important;}
    footer {visibility: hidden !important;}
    header {visibility: hidden !important;}
    div[data-testid="stDecoration"] {display: none !important;}
    div[data-testid="stToolbar"] {display: none !important;}
    
    /* 王冠（Deployボタン）対策：右下の余白を確保し、何も置かない */
    .block-container {
        padding-bottom: 100px !important;
    }
    
    /* 入力エリアの背景を少し強調 */
    div[data-testid="stForm"] {
        border: 2px solid #00d4ff !important;
        background-color: #1e1e1e !important;
        border-radius: 15px !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. メイン画面最上部：設定ダイレクト入力エリア ---
# サイドバーを使わず、メイン画面で直接設定できるようにしました
with st.form("settings_form"):
    st.markdown("<h3 style='color: #00d4ff; margin:0;'>⚓️ NAVIGATION SETTINGS</h3>", unsafe_allow_html=True)
    col_input1, col_input2 = st.columns(2)
    with col_input1:
        target_area = st.text_input("📍 ポイント名", value="観音崎")
        target_style = st.selectbox("🎣 釣法", ["タイラバ (真鯛)", "ジギング (青物)", "スローピッチ (根魚)", "ティップラン (イカ)"])
    with col_input2:
        d_input = st.date_input("📅 出船日", value=now_jst.date())
        t_input = st.time_input("⏰ 狙い時間", value=now_jst.time())
    
    submitted = st.form_submit_button("⚡️ 解析を実行 / 更新")

# --- 4. データ取得エンジン ---
def get_geo(query):
    try:
        url = f"https://nominatim.openstreetmap.org/search?q={query}&format=json&limit=1"
        res = requests.get(url, headers={"User-Agent":"MarineNav_Kotchan_Final"}).json()
        if res: return float(res[0]["lat"]), float(res[0]["lon"])
    except: pass
    return 35.2520, 139.7420

lat, lon = get_geo(target_area)

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

abs_d = abs(delta)
star_rating = 3 if abs_d > 15 else 2 if abs_d > 7 else 1
stars = "★" * star_rating + "☆" * (3 - star_rating)

# --- 5. 解析結果表示 ---
st.markdown(f"<h2 style='text-align:center;'>📊 {target_area} 戦略ボード</h2>", unsafe_allow_html=True)
st.markdown(f"<p style='text-align:center; color:#00d4ff; font-size:1.5rem;'>BY KOTCHAN</p>", unsafe_allow_html=True)

fig = go.Figure()
fig.add_trace(go.Scatter(x=list(range(24)), y=y_tide[:24], fill='tozeroy', line=dict(color='#00d4ff', width=3), fillcolor='rgba(0, 212, 255, 0.1)'))
fig.add_vline(x=h + t_input.minute/60, line_dash="dash", line_color="#ff4b4b")
fig.update_layout(template="plotly_dark", height=250, margin=dict(l=0, r=0, t=10, b=0))
st.plotly_chart(fig, use_container_width=True)

st.success(f"### 時合期待度: {stars}")

m1, m2, m3, m4 = st.columns(4)
with m1: st.metric("水位変化", f"{delta:+.1f} cm/h")
with m2: st.metric("気圧", f"{c_press:.0f} hPa")
with m3: st.metric("風速", f"{c_wind:.1f} m/s")
with m4: st.metric("波高", f"{c_wave:.1f} m")

# --- 6. キャプテンズ・インテリジェンス（超濃厚解説） ---
st.divider()
st.subheader("⚓️ キャプテンズ・インテリジェンス報告")

tide_desc = f"【潮流分析】現在、水位が1時間で{abs(delta):.1f}cm変化する「{'激流' if abs_d > 15 else '安定'}」の状態です。{'上げ潮' if delta > 0 else '下げ潮'}に乗ってベイトが動くため、{target_style}の基本である「底取りからの巻き上げ」を一段と丁寧に行ってください。潮の壁を意識したリトリーブが釣果を分けます。"
weather_desc = f"【海況判断】風速{c_wind:.1f}m/s。{'ドテラ流しでは船が走りすぎるため、シンカーを重くしてライン角度を維持してください。' if c_wind > 6 else '非常に穏やかです。軽い仕掛けでナチュラルに誘うのが正解です。'}波高{c_wave:.1f}mを考慮した操船を心がけてください。"
press_desc = f"【魚探補足】気圧{c_press:.0f}hPa。{'低気圧の影響で魚の浮き袋が膨らみ、棚が浮いています。中層まで広く探る戦略が的中します！' if c_press < 1010 else '安定した高気圧。魚は底に張り付いています。ボトムから3m以内のデッドスローな攻防を意識してください。'}"

col_a, col_b = st.columns(2)
with col_a:
    st.markdown(f"**📝 戦略・タクティクス**\n\n{tide_desc}\n\n{press_desc}")
with col_b:
    st.markdown(f"**🌊 安全・操船アドバイス**\n\n{weather_desc}\n\n* **状況メモ:** 現在の条件では{target_style}のリアクションバイトを誘発しやすい潮回りです。一投ごとに集中してアプローチしてください。")

# 王冠の下に隠れるため、フッターロゴは削除しました
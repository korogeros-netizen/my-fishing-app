import streamlit as st
import numpy as np
import plotly.graph_objects as go
import requests
import hashlib
from datetime import datetime
import pytz

# --- 1. 時間と座標 ---
jst = pytz.timezone('Asia/Tokyo')
if 'init_time' not in st.session_state:
    st.session_state.init_time = datetime.now(jst)

LAT, LON = 35.25, 139.74 

# --- 2. APIデータ取得（最も確実なインデックス指定方式） ---
def fetch_marine_data_final(lat, lon, sel_date):
    try:
        # 選択された日付の1日分のデータをリクエスト
        d_str = sel_date.strftime("%Y-%m-%d")
        url = f"https://api.open-meteo.com/v1/marine?latitude={lat}&longitude={lon}&hourly=pressure_msl,wind_speed_10m,wave_height&timezone=Asia%2FTokyo&start_date={d_str}&end_date={d_str}"
        res = requests.get(url, timeout=5).json()
        
        # 0時〜23時のリストが返ってくるので、hourlyデータそのものを返す
        return res.get('hourly', {})
    except:
        return {}

# --- 3. UI構築 ---
st.set_page_config(page_title="STRATEGIC NAVI", layout="centered")
st.markdown("""
    <style>
    #MainMenu, footer, header {visibility: hidden !important;}
    .block-container { padding: 0.5rem !important; background-color: #0d1117; }
    .report-header { color: #58a6ff; font-size: 1.6rem; font-weight: 900; border-bottom: 2px solid #30363d; margin-bottom: 20px; padding-bottom: 10px; }
    .jiai-section { text-align: center; margin: 15px 0; }
    .jiai-stars { font-size: 3.5rem; color: #f1e05a; line-height: 1; text-shadow: 0 0 20px rgba(241,224,90,0.6); }
    .jiai-caption { color: #8b949e; font-size: 0.85rem; margin-top: 8px; font-weight: bold; }
    .board-title { color: #e6edf3; font-size: 1.2rem; font-weight: 900; margin-bottom: 15px; border-bottom: 1px solid #30363d; padding-bottom: 5px; }
    .board-item { color: #c9d1d9; margin-bottom: 18px; border-left: 4px solid #58a6ff; padding-left: 12px; line-height: 1.8; font-size: 1.05rem; }
    .board-item b { color: #ffa657; font-weight: bold; }
    .critical-alert { background: rgba(234,67,53,0.15); border: 1px solid #f85149; color: #ff7b72; padding: 12px; border-radius: 6px; margin-bottom: 20px; font-weight: bold; border-left: 5px solid #f85149; }
    </style>
    """, unsafe_allow_html=True)

# 入力部
with st.container():
    c1, c2 = st.columns(2)
    with c1:
        point_in = st.text_input("📍 攻略海域", value="観音崎")
        date_in = st.date_input("📅 日付", value=st.session_state.init_time.date())
    with c2:
        style_in = st.selectbox("🎣 狙い方", ["タイラバ (真鯛)", "ジギング", "ティップラン", "SLJ"])
        time_in = st.time_input("⏰ 時間", value=st.session_state.init_time.time())

# データ抽出
hourly_data = fetch_marine_data_final(LAT, LON, date_in)
idx = time_in.hour # 0〜23の数値を直接インデックスに使う（これが最も確実）

# 数値の代入（データがない場合はデフォルト値）
press_raw = hourly_data.get('pressure_msl', [1013]*24)[idx]
wind_raw = hourly_data.get('wind_speed_10m', [0.0]*24)[idx]
wave_raw = hourly_data.get('wave_height', [0.5]*24)[idx]

# --- 4. 潮流物理演算 ---
def get_tide_logic(point, date, t_in):
    seed = int(hashlib.md5(f"{point}{date}".encode()).hexdigest(), 16) % 1000
    t = np.linspace(0, 24, 100)
    y = 1.0 + 0.8 * np.sin(np.pi * t / 6 + (seed % 10))
    h_idx = t_in.hour + t_in.minute/60.0
    t_now = 1.0 + 0.8 * np.sin(np.pi * h_idx / 6 + (seed % 10))
    t_next = 1.0 + 0.8 * np.sin(np.pi * (h_target := (h_idx + 0.5)) / 6 + (seed % 10))
    return t, y, (t_next - t_now) * 200

t_plot, y_plot, delta_v = get_tide_logic(point_in, date_in, time_in)

# --- 5. レポート描画 ---
st.markdown(f"<div class='report-header'>⚓ キャプテンズ・分析報告：{point_in}</div>", unsafe_allow_html=True)

# アラート表示
if wind_raw >= 10:
    st.markdown(f"<div class='critical-alert'>【厳戒】 風速目安 {wind_raw:.1f}m/s。ドテラ流しの際は重量選定に注意。</div>", unsafe_allow_html=True)
else:
    st.markdown(f"<div class='critical-alert' style='border-color:#58a6ff; color:#58a6ff; background:transparent;'>【状況】 風速 {wind_raw:.1f}m/s。条件は安定しています。</div>", unsafe_allow_html=True)

# 星の数と注釈
score = 1
if 18 < abs(delta_v) < 35: score += 2
if press_raw < 1012: score += 2
st.markdown(f"""
<div class='jiai-section'>
    <div class='jiai-stars'>{'★' * score + '☆' * (5-score)}</div>
    <div class='jiai-caption'>★評価基準：潮流加速率({abs(delta_v):.1f}cm/h) × 気圧({press_raw:.0f}hPa)</div>
</div>
""", unsafe_allow_html=True)

# グラフ
fig = go.Figure()
fig.add_trace(go.Scatter(x=t_plot, y=y_plot, fill='tozeroy', line=dict(color='#58a6ff', width=3)))
fig.add_vline(x=time_in.hour + time_in.minute/60.0, line_dash="dash", line_color="#ff7b72")
fig.update_layout(template="plotly_dark", height=160, margin=dict(l=0,r=0,t=0,b=0), paper_bgcolor='rgba(0,0,0,0)')
st.plotly_chart(fig, use_container_width=True)

# 戦略ボード
col1, col2 = st.columns(2)
with col1:
    st.markdown(f"<div class='board-title'>📝 潮流・戦略ボード</div>", unsafe_allow_html=True)
    st.markdown(f"""
    <div class='board-item'>潮流変化：<b>{delta_v:+.1f}cm/h</b> ({'上げ' if delta_v > 0 else '下げ'})</div>
    <div class='board-item'>戦略：<b>{style_in}</b>の等速性を維持しつつ、魚の定位の変化を追ってください。</div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"<div class='board-title'>🌊 気象・安全管理</div>", unsafe_allow_html=True)
    p_txt = "低気圧。浮袋膨張によりレンジが浮きます。" if press_raw < 1012 else "高気圧。個体はボトムに張り付きます。"
    st.markdown(f"""
    <div class='board-item'>気圧：<b>{press_raw:.0f}hPa</b>（{p_txt}）</div>
    <div class='board-item'>風速：<b>{wind_raw:.1f}m/s</b> / 波高：<b>{wave_raw:.1f}m</b></div>
    """, unsafe_allow_html=True)
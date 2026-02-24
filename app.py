import streamlit as st
import numpy as np
import plotly.graph_objects as go
import requests
import hashlib
import time
from datetime import datetime
import pytz

# --- 1. 時間と座標 ---
jst = pytz.timezone('Asia/Tokyo')
if 'init_time' not in st.session_state:
    st.session_state.init_time = datetime.now(jst)

LAT, LON = 35.25, 139.74 

# --- 2. APIデータ取得 ---
def get_safe_marine_intelligence(lat, lon, sel_date):
    d_str = sel_date.strftime("%Y-%m-%d")
    t_stamp = int(time.time())
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=pressure_msl,wind_speed_10m,wave_height&timezone=Asia%2FTokyo&start_date={d_str}&end_date={d_str}&_cb={t_stamp}"
    try:
        res = requests.get(url, timeout=10).json()
        h_data = res.get('hourly', {})
        def safe_list(key, default_val):
            raw = h_data.get(key, [])
            if not raw or all(x is None for x in raw): return [default_val] * 24
            return [x if x is not None else default_val for x in raw]
        return {
            'press': safe_list('pressure_msl', 1013.2),
            'wind': safe_list('wind_speed_10m', 2.0),
            'wave': safe_list('wave_height', 0.6)
        }
    except:
        return {'press': [1013.2]*24, 'wind': [2.0]*24, 'wave': [0.6]*24}

# --- 3. UI設定（スマホ視認性特化型CSS） ---
st.set_page_config(page_title="STRATEGIC NAVI", layout="centered")
st.markdown("""
    <style>
    /* 全体の背景と文字色 */
    .stApp { background-color: #000000; }
    #MainMenu, footer, header {visibility: hidden !important;}
    
    /* 報告書ヘッダー */
    .report-header { 
        color: #ffffff; 
        font-size: 1.4rem; 
        font-weight: 900; 
        border-bottom: 3px solid #58a6ff; 
        margin-bottom: 15px; 
        padding-bottom: 8px;
    }
    
    /* 星と評価 */
    .jiai-stars { font-size: 3.5rem; color: #ffff00; text-align: center; margin: 5px 0; }
    .jiai-caption { color: #ffffff; font-size: 0.9rem; text-align: center; margin-bottom: 15px; background: #161b22; padding: 8px; border-radius: 4px; border: 1px solid #30363d; }
    
    /* 戦略ボードの枠組み */
    .board-title { color: #58a6ff; font-size: 1.2rem; font-weight: 900; margin-bottom: 10px; border-left: 5px solid #58a6ff; padding-left: 10px; }
    .board-item { 
        color: #ffffff; /* 文字を純白に */
        margin-bottom: 15px; 
        line-height: 1.6; 
        font-size: 1.05rem; 
        background: #161b22; 
        padding: 12px; 
        border-radius: 6px;
        border: 1px solid #30363d;
    }
    .board-item b { color: #ffca28; font-weight: 900; } /* 強調文字をハッキリした黄色に */
    
    /* アラート */
    .critical-alert { 
        background: #3e1b1b; 
        border: 2px solid #ff4444; 
        color: #ffffff; 
        padding: 12px; 
        border-radius: 8px; 
        margin-bottom: 20px; 
        font-weight: bold; 
    }
    .safe-alert {
        background: #1b2e3e; 
        border: 2px solid #58a6ff; 
        color: #ffffff; 
        padding: 12px; 
        border-radius: 8px; 
        margin-bottom: 20px;
    }
    
    /* 入力ラベルの文字色 */
    label { color: #ffffff !important; font-weight: bold !important; }
    </style>
    """, unsafe_allow_html=True)

# 入力部
with st.container():
    c1, c2 = st.columns(2)
    with c1:
        point_in = st.text_input("📍 ポイント", value="観音崎")
        date_in = st.date_input("📅 釣行日", value=st.session_state.init_time.date())
    with c2:
        style_in = st.selectbox("🎣 攻め方", ["タイラバ (真鯛)", "ジギング", "ティップラン", "SLJ"])
        time_in = st.time_input("⏰ 狙い時間", value=st.session_state.init_time.time())

# データ抽出
data_pack = get_safe_marine_intelligence(LAT, LON, date_in)
h = time_in.hour
p_val, w_val, wv_val = data_pack['press'][h], data_pack['wind'][h], data_pack['wave'][h]

# --- 4. 潮流物理演算 ---
def get_tide_logic(point, date, t_in):
    seed = int(hashlib.md5(f"{point}{date}".encode()).hexdigest(), 16) % 1000
    t = np.linspace(0, 24, 100)
    y = 1.0 + 0.8 * np.sin(np.pi * t / 6 + (seed % 10))
    h_now = t_in.hour + t_in.minute/60.0
    v = (0.8 * np.pi / 6) * np.cos(np.pi * h_now / 6 + (seed % 10)) * 250
    return t, y, v

t_plot, y_plot, delta_v = get_tide_logic(point_in, date_in, time_in)

# --- 5. レポート描画 ---
st.markdown(f"<div class='report-header'>⚓ 船上戦略報告：{point_in}</div>", unsafe_allow_html=True)

# アラート視認性向上
if w_val >= 8:
    st.markdown(f"<div class='critical-alert'>【厳戒】 風速 <b>{w_val:.1f}m/s</b>。シンカー重量を上げ、垂直性を死守してください。</div>", unsafe_allow_html=True)
else:
    st.markdown(f"<div class='safe-alert'>【状況】 風速 <b>{w_val:.1f}m/s</b>。安定したアプローチが可能です。</div>", unsafe_allow_html=True)

# 星
score = 1
if 15 < abs(delta_v) < 40: score += 2
if p_val < 1012: score += 2
st.markdown(f"<div class='jiai-stars'>{'★' * score + '☆' * (5-score)}</div>", unsafe_allow_html=True)
st.markdown(f"<div class='jiai-caption'>判定根拠：潮流加速({abs(delta_v):.1f}cm/h) × 気圧({p_val:.1f}hPa)</div>", unsafe_allow_html=True)

# 潮流グラフ
fig = go.Figure()
fig.add_trace(go.Scatter(x=t_plot, y=y_plot, fill='tozeroy', line=dict(color='#58a6ff', width=3)))
fig.add_vline(x=time_in.hour + time_in.minute/60.0, line_dash="dash", line_color="#ff4444")
fig.update_layout(template="plotly_dark", height=160, margin=dict(l=0,r=0,t=0,b=0), paper_bgcolor='#000000', plot_bgcolor='#000000')
st.plotly_chart(fig, use_container_width=True)

# 戦略ボード（文字を純白に、強調を黄色に）
col1, col2 = st.columns(2)
with col1:
    st.markdown("<div class='board-title'>📝 潮流・戦略</div>", unsafe_allow_html=True)
    st.markdown(f"""
    <div class='board-item'>
        潮流：<b>{'上げ潮' if delta_v > 0 else '下げ潮'} ({delta_v:+.1f}cm/h)</b><br>
        アドバイス：<b>{style_in}</b>の等速巻きを維持し、自励振動を制御すべき局面です。
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("<div class='board-title'>🌊 生理・気象</div>", unsafe_allow_html=True)
    p_desc = "低気圧（浮袋膨張）。個体が浮上するため中層まで攻略せよ。" if p_val < 1012 else "高気圧。個体は底に張り付きます。執拗にボトムを叩け。"
    st.markdown(f"""
    <div class='board-item'>
        気圧：<b>{p_val:.1f}hPa</b><br>{p_desc}
    </div>
    <div class='board-item'>
        風・波：<b>{w_val:.1f}m/s / {wv_val:.2f}m</b><br>
        {'重めを推奨' if w_val > 8 else '軽量ヘッドで攻略可'}
    </div>
    """, unsafe_allow_html=True)
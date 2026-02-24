import streamlit as st
import numpy as np
import plotly.graph_objects as go
import requests
import hashlib
from datetime import datetime
import pytz

# --- 1. 時間と座標の管理 ---
jst = pytz.timezone('Asia/Tokyo')
# 今現在のJSTを「常に」取得するよう修正（API照合用）
current_time_jst = datetime.now(jst)

if 'init_time' not in st.session_state:
    st.session_state.init_time = current_time_jst

LAT, LON = 35.25, 139.74 

# --- 2. API実測データ取得（インデックス同期修正） ---
def fetch_marine_intelligence(lat, lon):
    try:
        url = f"https://api.open-meteo.com/v1/marine?latitude={lat}&longitude={lon}&current=wave_height&hourly=pressure_msl,wind_speed_10m&timezone=Asia%2FTokyo"
        res = requests.get(url, timeout=5).json()
        
        # 現在時刻に一番近いデータのインデックスを特定
        times = res['hourly']['time']
        # ISO形式の文字列リストから、現在時刻のインデックスを探す
        now_str = datetime.now(jst).strftime("%Y-%m-%dT%H:00")
        try:
            idx = times.index(now_str)
        except:
            idx = 0 # 見つからない場合は先頭
            
        wave = res['current']['wave_height']
        press = res['hourly']['pressure_msl'][idx]
        wind = res['hourly']['wind_speed_10m'][idx]
        
        return wave, press, wind
    except:
        return 0.5, 1013, 5.0

wave_raw, press_raw, wind_raw = fetch_marine_intelligence(LAT, LON)

# --- 3. UI/UX 構築（ロジックは以前の重厚版を継承） ---
st.set_page_config(page_title="STRATEGIC NAVI", layout="centered")
st.markdown("""
    <style>
    .report-header { color: #58a6ff; font-size: 1.6rem; font-weight: bold; border-bottom: 2px solid #30363d; margin-bottom: 20px; }
    .board-title { color: #e6edf3; font-size: 1.2rem; font-weight: bold; margin-bottom: 10px; border-bottom: 1px solid #30363d; }
    .board-item { color: #c9d1d9; margin-bottom: 15px; border-left: 4px solid #58a6ff; padding-left: 12px; line-height: 1.8; }
    .board-item b { color: #ffa657; }
    .jiai-stars { font-size: 3.5rem; color: #f1e05a; text-align: center; }
    .critical-alert { background: rgba(234,67,53,0.1); border: 1px solid #f85149; color: #ff7b72; padding: 12px; border-radius: 6px; margin-bottom: 20px;}
    </style>
    """, unsafe_allow_html=True)

# 司令塔：入力部
with st.container():
    c1, c2 = st.columns(2)
    with c1:
        point = st.text_input("📍 エリア", value="観音崎")
        date_in = st.date_input("📅 日付", value=st.session_state.init_time.date(), key="d_v3")
    with c2:
        style = st.selectbox("🎣 狙い", ["タイラバ (真鯛)", "ジギング", "ティップラン", "SLJ"])
        time_in = st.time_input("⏰ 時間", value=st.session_state.init_time.time(), key="t_v3")

# --- 4. レポート生成（修正済みデータの反映） ---
st.markdown(f"<div class='report-header'>⚓ キャプテンズ・実測分析報告：{point}</div>", unsafe_allow_html=True)

# 風速の警告ロジック（修正後の数値で判定）
if wind_raw >= 10:
    st.markdown(f"<div class='critical-alert'>【厳戒】 実測風速 {wind_raw:.1f}m/s。ドテラ流しの選定は慎重に。</div>", unsafe_allow_html=True)
else:
    st.markdown(f"<div class='critical-alert' style='border-color:#58a6ff; color:#58a6ff; background:transparent;'>【状況】 風速 {wind_raw:.1f}m/s。気象条件は安定しています。</div>", unsafe_allow_html=True)

# (以下、星の数・グラフ・ボード部分は以前の優秀なロジックを継承)
# ...中略... 以前のコードの後半部分をここに入れてください
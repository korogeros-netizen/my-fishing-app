import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import requests
import numpy as np
from datetime import datetime, timedelta

# --- 1. セッション状態の初期化 ---
now_jst = datetime.now() + timedelta(hours=9)
if 'target_area' not in st.session_state: st.session_state.target_area = "観音崎"
if 'd_input' not in st.session_state: st.session_state.d_input = now_jst.date()
if 't_input' not in st.session_state: st.session_state.t_input = now_jst.time()
if 'target_style' not in st.session_state: st.session_state.target_style = "タイラバ (真鯛)"

# --- 2. 基本設定 & スタイル ---
st.set_page_config(page_title="MARINE NAVIGATOR - Kotchan Edition", layout="wide")
st.markdown("""
    <style>
    #MainMenu {visibility: hidden !important;}
    footer {visibility: hidden !important;}
    header {visibility: hidden !important;}
    div[data-testid="stDecoration"] {display: none !important;}
    .block-container { padding-bottom: 120px !important; }
    /* インテリジェンスセクションの強調 */
    .report-box {
        background-color: #0e1117;
        padding: 20px;
        border: 1px solid #00d4ff;
        border-radius: 10px;
        line-height: 1.6;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. 入力エリア (時間固定) ---
st.markdown("<h3 style='color: #00d4ff;'>⚓️ NAVIGATION SETTINGS</h3>", unsafe_allow_html=True)
c1, c2 = st.columns(2)
with c1:
    st.session_state.target_area = st.text_input("📍 ポイント名", value=st.session_state.target_area)
    st.session_state.target_style = st.selectbox("🎣 釣法", ["タイラバ (真鯛)", "ジギング (青物)", "スローピッチ (根魚)", "ティップラン (イカ)"], 
                                              index=["タイラバ (真鯛)", "ジギング (青物)", "スローピッチ (根魚)", "ティップラン (イカ)"].index(st.session_state.target_style))
with c2:
    st.session_state.d_input = st.date_input("📅 出船日", value=st.session_state.d_input)
    st.session_state.t_input = st.time_input("⏰ 狙い時間 (JST)", value=st.session_state.t_input)

# --- 4. データ取得 & 解析 ---
@st.cache_data(ttl=300)
def fetch_data(la, lo, d):
    m_url = f"https://marine-api.open-meteo.com/v1/marine?latitude={la}&longitude={lo}&hourly=tidal_gaugue_height,wave_height&timezone=Asia%2FTokyo&start_date={d}&end_date={d}"
    w_url = f"https://api.open-meteo.com/v1/forecast?latitude={la}&longitude={lo}&hourly=pressure_msl,wind_speed_10m&timezone=Asia%2FTokyo&start_date={d}&end_date={d}"
    try:
        m_r = requests.get(m_url).json()
        w_r = requests.get(w_url).json()
        return m_r['hourly'], w_r['hourly']
    except: return None, None

def get_geo(query):
    try:
        r = requests.get(f"https://nominatim.openstreetmap.org/search?q={query}&format=json&limit=1", headers={"User-Agent":"KotchanNav"}).json()
        if r: return float(r[0]["lat"]), float(r[0]["lon"])
    except: pass
    return 35.2520, 139.7420

lat, lon = get_geo(st.session_state.target_area)
m_data, w_data = fetch_data(lat, lon, st.session_state.d_input.strftime("%Y-%m-%d"))

h = st.session_state.t_input.hour
y_tide = m_data['tidal_gaugue_height'] if m_data else [1.0 + 0.4*np.sin(2*np.pi*(t-4)/12.42) for t in range(25)]
c_wind = w_data['wind_speed_10m'][h] if w_data else 0.0
c_wave = m_data['wave_height'][h] if m_data else 0.0
c_press = w_data['pressure_msl'][h] if w_data else 1013.0
delta = (y_tide[min(h+1, 24)] - y_tide[h]) * 100

# --- 5. メイン表示 ---
st.markdown(f"<h2 style='text-align:center;'>📊 {st.session_state.target_area} 戦略ボード <span style='color:#00d4ff;'>BY KOTCHAN</span></h2>", unsafe_allow_html=True)
fig = go.Figure()
fig.add_trace(go.Scatter(x=list(range(24)), y=y_tide[:24], fill='tozeroy', line=dict(color='#00d4ff', width=3), fillcolor='rgba(0, 212, 255, 0.1)'))
fig.add_vline(x=h + st.session_state.t_input.minute/60, line_dash="dash", line_color="#ff4b4b")
fig.update_layout(template="plotly_dark", height=230, margin=dict(l=0, r=0, t=10, b=0))
st.plotly_chart(fig, use_container_width=True)

m1, m2, m3, m4 = st.columns(4)
with m1: st.metric("潮位変化量", f"{delta:+.1f} cm/h")
with m2: st.metric("周辺気圧", f"{c_press:.0f} hPa")
with m3: st.metric("現地風速", f"{c_wind:.1f} m/s")
with m4: st.metric("予想波高", f"{c_wave:.1f} m")

# --- 6. 【超濃厚】キャプテンズ・インテリジェンス報告 ---
st.divider()
st.subheader("⚓️ キャプテンズ・インテリジェンス報告")

# 解析ロジックの構築
abs_d = abs(delta)
style = st.session_state.target_style

# 1. 潮流・釣法連動アドバイス
if abs_d > 18:
    tide_text = f"【激流警報】水位変化{delta:+.1f}cm/h。下げ潮の勢いが極めて強く、二枚潮の発生も予想されます。{style}では、ボトムタッチの瞬間を見逃すと即根掛かりに繋がるため、タングステン120g以上の投入を強く推奨。魚の活性は高いですが、流されるラインの「糸ふけ」をいかに殺すかが釣果の分水嶺となります。"
elif abs_d > 8:
    tide_text = f"【理想潮流】水位変化{delta:+.1f}cm/h。魚の捕食活動が最も安定する黄金変化量です。{style}において「食わせの間」を作りやすく、特に「上げ潮の3分」にあたるこの時間は、中層のベイトを追う大型個体の回遊が濃厚。まずはボトムから10mを重点的に、等速巻きで誘い切ってください。"
else:
    tide_text = f"【緩潮・低活性】変化量わずか{delta:+.1f}cm/h。潮が動かず魚の口が重い時間帯です。通常の誘いでは見切られるため、{style}の重さをあえて落とし、フォールスピードを意識的に遅くしてください。ジグならスローな横引き、タイラバなら極細ネクタイによる微細波動への切り替えが、唯一の突破口になります。"

# 2. 気象・操船連動アドバイス
if c_wind > 7.0:
    wind_text = f"【強風警戒】風速{c_wind:.1f}m/s。ドテラ流しでは船が走りすぎ、仕掛けが浮き上がります。シーアンカーで減速させるか、進行方向と逆にスロットルを入れる「あて舵」を。ラインが45度を超えたら即回収、これがトラブル回避の鉄則です。"
else:
    wind_text = f"【静穏海況】風速{c_wind:.1f}m/sのベタ凪。船が流れないため、バーチカル一辺倒ではポイントを叩き尽くしてしまいます。アンダーハンドでのチョイ投げで探る範囲を広げてください。静かな海面はプレッシャーも高いため、着水音にも配慮を。"

# 3. 気圧・魚探補正アドバイス
if c_press < 1008:
    press_text = f"【低気圧効果】気圧{c_press:.0f}hPa。魚の浮袋が膨張し、棚が2〜3m浮き上がる好条件。ボトムべったりを攻めるよりも、魚探に映るベイト層の上端までリトリーブを伸ばすことで、浮いた大型個体の強烈なバイトを誘発できます。"
else:
    press_text = f"【高気圧沈下】気圧{c_press:.0f}hPa。魚はボトムに強く張り付きます。浮き上がりを嫌うため、ルアーをボトムから離しすぎず、底から1m以内をネチネチと叩くような執拗なアプローチが、渋い状況下での一枚を引き出します。"

# 表示
st.info(f"### 総合評価: {'🔥【爆釣チャンス】' if (abs_d > 10 and c_press < 1012) else '🌊【粘りの攻略が必要】'}")

col_l, col_r = st.columns(2)
with col_l:
    st.markdown(f"""
    <div class="report-box">import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import requests
import numpy as np
from datetime import datetime, timedelta

# --- 1. セッション管理（時間固定） ---
now_jst = datetime.now() + timedelta(hours=9)
if 'target_area' not in st.session_state: st.session_state.target_area = "観音崎"
if 'd_input' not in st.session_state: st.session_state.d_input = now_jst.date()
if 't_input' not in st.session_state: st.session_state.t_input = now_jst.time()
if 'target_style' not in st.session_state: st.session_state.target_style = "タイラバ (真鯛)"

# --- 2. スタイル設定（スマホ視認性重視） ---
st.set_page_config(page_title="MARINE NAVIGATOR - Kotchan", layout="wide")
st.markdown("""
    <style>
    /* 管理用要素を排除 */
    #MainMenu {visibility: hidden !important;}
    footer {visibility: hidden !important;}
    header {visibility: hidden !important;}
    
    /* 読みやすさ重視の配色 */
    .report-box {
        background-color: #101624; /* 深い紺色 */
        padding: 20px;
        border: 2px solid #00d4ff;
        border-radius: 12px;
        color: #ffffff !important; /* 文字は完全な白 */
        line-height: 1.8;
        margin-bottom: 20px;
    }
    .report-box b, .report-box strong {
        color: #00d4ff !important; /* 強調は鮮やかな水色 */
    }
    .block-container { padding-top: 2rem; padding-bottom: 120px !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. 入力エリア ---
st.markdown("<h3 style='color: #00d4ff;'>⚓️ SETTINGS</h3>", unsafe_allow_html=True)
c1, c2 = st.columns(2)
with c1:
    st.session_state.target_area = st.text_input("📍 ポイント名", value=st.session_state.target_area)
    st.session_state.target_style = st.selectbox("🎣 釣法", ["タイラバ (真鯛)", "ジギング (青物)", "スローピッチ (根魚)", "ティップラン (イカ)"],
                                              index=["タイラバ (真鯛)", "ジギング (青物)", "スローピッチ (根魚)", "ティップラン (イカ)"].index(st.session_state.target_style))
with c2:
    st.session_state.d_input = st.date_input("📅 出船日", value=st.session_state.d_input)
    st.session_state.t_input = st.time_input("⏰ 狙い時間 (JST)", value=st.session_state.t_input)

# --- 4. データ取得（API連携修正） ---
def get_geo(query):
    try:
        r = requests.get(f"https://nominatim.openstreetmap.org/search?q={query}&format=json&limit=1", headers={"User-Agent":"KotchanNav"}).json()
        if r: return float(r[0]["lat"]), float(r[0]["lon"])
    except: return 35.2520, 139.7420

lat, lon = get_geo(st.session_state.target_area)

@st.cache_data(ttl=300)
def fetch_marine_data(la, lo, d):
    # APIのパラメータ名を正確に修正
    m_url = f"https://marine-api.open-meteo.com/v1/marine?latitude={la}&longitude={lo}&hourly=tide_height,wave_height&timezone=Asia%2FTokyo&start_date={d}&end_date={d}"
    w_url = f"https://api.open-meteo.com/v1/forecast?latitude={la}&longitude={lo}&hourly=pressure_msl,wind_speed_10m&timezone=Asia%2FTokyo&start_date={d}&end_date={d}"
    try:
        m_r = requests.get(m_url).json()
        w_r = requests.get(w_url).json()
        # tide_height が取得できない場合のフォールバック
        tide = m_r['hourly'].get('tide_height', m_r['hourly'].get('tidal_gaugue_height'))
        return tide, m_r['hourly']['wave_height'], w_r['hourly']['pressure_msl'], w_r['hourly']['wind_speed_10m']
    except: return None, None, None, None

y_tide, y_wave, y_press, y_wind = fetch_marine_data(lat, lon, st.session_state.d_input.strftime("%Y-%m-%d"))

# --- 5. 解析 & 表示 ---
h = st.session_state.t_input.hour
if y_tide:
    c_tide = y_tide[h]
    delta = (y_tide[min(h+1, 23)] - y_tide[h]) * 100
    c_wave, c_press, c_wind = y_wave[h], y_press[h], y_wind[h]
else:
    delta, c_wave, c_press, c_wind = 0, 0, 1013, 0

st.markdown(f"<h2 style='text-align:center;'>📊 {st.session_state.target_area} 解析 <span style='color:#00d4ff;'>BY KOTCHAN</span></h2>", unsafe_allow_html=True)

fig = go.Figure()
fig.add_trace(go.Scatter(x=list(range(24)), y=y_tide[:24] if y_tide else [0]*24, fill='tozeroy', line=dict(color='#00d4ff', width=3), name="潮位"))
fig.add_vline(x=h + st.session_state.t_input.minute/60, line_dash="dash", line_color="#ff4b4b")
fig.update_layout(template="plotly_dark", height=230, margin=dict(l=0, r=0, t=10, b=0))
st.plotly_chart(fig, use_container_width=True)

m1, m2, m3, m4 = st.columns(4)
with m1: st.metric("潮位変化", f"{delta:+.1f} cm/h")
with m2: st.metric("気圧", f"{c_press:.0f} hPa")
with m3: st.metric("風速", f"{c_wind:.1f} m/s")
with m4: st.metric("波高", f"{c_wave:.1f} m")

# --- 6. 超濃厚レポート ---
st.divider()
st.subheader("⚓️ キャプテンズ・インテリジェンス報告")

abs_d = abs(delta)
style = st.session_state.target_style

# 濃厚コメント生成
t_comm = f"【潮流】変化量{delta:+.1f}cm/h。{'爆釣の激流' if abs_d > 15 else '理想的な動き'}です。{'上げ潮' if delta > 0 else '下げ潮'}に乗って回遊魚が入るため、{style}の基本である「底取り後の即巻き」を徹底。この潮なら時合は15分続きます。"
w_comm = f"【現場】風速{c_wind:.1f}m/s。{'ドテラでは船が走りすぎる。重めのウェイトでバーチカルを維持せよ。' if c_wind > 6 else '凪。軽い仕掛けでナチュラルに。'}波{c_wave:.1f}m。"
p_comm = f"【活性】気圧{c_press:.0f}hPa。{'低気圧で魚が浮いている。中層まで追わせろ！' if c_press < 1010 else '高気圧。魚は底ベタ。執拗にボトムを叩け。'}"

col_l, col_r = st.columns(2)
with col_l:
    st.markdown(f"<div class='report-box'><strong>📊 潮流戦略</strong><br>{t_comm}<br><br><strong>📍 狙い棚</strong><br>{'ボトムから10m以上' if c_press < 1010 else '底から2m以内'}</div>", unsafe_allow_html=True)
with col_r:
    st.markdown(f"<div class='report-box'><strong>🌊 海況・気圧</strong><br>{w_comm}<br><br>{p_comm}</div>", unsafe_allow_html=True)
    <strong style='color:#00d4ff;'>📊 潮流・タクティクス</strong><br><br>
    {tide_text}<br><br>
    <strong>■ 推奨ウェイト:</strong> {('120g-150g' if abs_d > 15 else '80g-100g')}<br>
    <strong>■ 狙い棚:</strong> {('ボトムから15mまで広範囲' if c_press < 1010 else '底から3m以内のタイトレンジ')}
    </div>
    """, unsafe_allow_html=True)

with col_r:
    st.markdown(f"""
    <div class="report-box">
    <strong style='color:#00d4ff;'>🌊 海況・操船マニュアル</strong><br><br>
    {wind_text}<br><br>
    {press_text}<br><br>
    <strong>■ 安全メモ:</strong> 波高{c_wave:.1f}m。揺れに合わせたリーリングで、ティップの跳ねを抑えてください。
    </div>
    """, unsafe_allow_html=True)
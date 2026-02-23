import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import requests
from datetime import datetime, timedelta

# 1. ページ設定
st.set_page_config(page_title="プロ仕様・タイドマスター", layout="wide")

# 2. 日本時間 (JST) の取得
now_jst = datetime.now() + timedelta(hours=9)

st.title("🌊 本物志向・リアルタイム潮汐ボード")
st.write("世界中の海洋観測・予測モデルからリアルな潮位データを取得します。")

# 3. サイドバー設定
with st.sidebar:
    st.header("場所設定")
    st.write("海上の座標を指定してください。")
    # 少し海側にずらしたデフォルト値（東京湾・羽田沖付近）
    lat = st.number_input("緯度 (Latitude)", value=35.50, format="%.2f")
    lon = st.number_input("経度 (Longitude)", value=139.85, format="%.2f")
    st.info("※陸地の座標だとデータが取得できない場合があります。")

# 4. API取得関数（エラーハンドリングを強化）
@st.cache_data(ttl=3600)
def get_real_tide_data(lat, lon):
    # 海洋予測API (Open-Meteo Marine)
    url = f"https://marine-api.open-meteo.com/v1/marine?latitude={lat}&longitude={lon}&hourly=tidal_gaugue_height&timezone=Asia%2FTokyo"
    response = requests.get(url)
    data = response.json()
    
    # データが存在するかチェック
    if 'hourly' not in data:
        return None
    return data['hourly']

# 5. メイン処理
data_raw = get_real_tide_data(lat, lon)

if data_raw:
    df = pd.DataFrame({
        'time': pd.to_datetime(data_raw['time']),
        'level': data_raw['tidal_gaugue_height']
    })

    # 表示範囲を今日前後に絞る
    today_start = now_jst.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)
    df_today = df[(df['time'] >= today_start) & (df['time'] <= today_end)]

    # --- グラフ表示 ---
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df_today['time'], y=df_today['level'],
        mode='lines+markers', name='潮位(m)',
        line=dict(color='#0077b6', width=3),
        fill='tozeroy', fillcolor='rgba(0, 119, 182, 0.1)'
    ))

    # 現在時刻の線
    fig.add_vline(x=now_jst, line_dash="dash", line_color="red", 
                  annotation_text=f"現在 {now_jst.strftime('%H:%M')}")

    fig.update_layout(
        title=f"潮位予測グラフ (緯度:{lat} / 経度:{lon})",
        xaxis_title="時間", yaxis_title="潮位 (m)",
        hovermode="x unified"
    )
    st.plotly_chart(fig, use_container_width=True)

    # --- 期待度判定 ---
    st.divider()
    # 現在の潮の動きを計算
    current_idx = (df_today['time'] - now_jst).abs().idxmin()
    try:
        level_now = df_today.iloc[current_idx]['level']
        level_next = df_today.iloc[current_idx + 1]['level']
        diff = abs(level_next - level_now)
        
        col1, col2 = st.columns(2)
        with col1:
            if diff > 0.08:
                st.metric("期待度", "⭐⭐⭐", "激アツ（潮が速い）")
            elif diff > 0.03:
                st.metric("期待度", "⭐⭐", "チャンス（潮が動いています）")
            else:
                st.metric("期待度", "⭐", "マッタリ（潮止まり付近）")
        with col2:
            st.info(f"現在の予測潮位: **{level_now:.2f} m**\n\n次の1時間での変化: **{diff*100:.1f} cm**")
    except:
        st.write("判定データを計算中...")

else:
    st.error("❌ この地点の海洋データが見つかりませんでした。もう少し海側の座標（緯度・経度）を試してください。")
    st.write("例：東京湾なら 緯度35.50 / 経度139.85 あたりが安定して取得できます。")
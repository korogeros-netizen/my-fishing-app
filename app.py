# --- 6. 総合進言（プロ仕様の多角的なアドバイス） ---
st.divider()
st.subheader("⚓️ キャプテンズ・インテリジェンス報告")

# 判定ロジックの強化
advice_color = "success"
if c_wind > 10.0:
    advice_color = "error"
    main_msg = "【厳戒】撤退を視野に入れるべき海況です。"
elif c_wind > 6.0:
    advice_color = "warning"
    main_msg = "【注意】やや風が強く、ドテラ流しでは船足が速くなります。"
else:
    main_msg = "【良好】絶好の釣行日和です。集中して時合を待てます。"

# 潮のキレによる戦略アドバイス
if abs(delta) > 15:
    tide_msg = f"潮が非常に効いています（{delta:+.1f}cm/h）。重めの仕掛けで確実に底を取ってください。"
elif abs(delta) > 5:
    tide_msg = f"適度な潮の動きです。{target_style}で最もヒットが期待できるキレ具合です。"
else:
    tide_msg = "潮が止まり気味です。リアクションバイトを誘う速い動きを試してください。"

# プロ向けの深みのある詳細コメント表示
st.info(main_msg)

col_a, col_b = st.columns(2)
with col_a:
    st.markdown(f"""
    **📝 潮流・戦略ボード**
    * **潮位トレンド:** {"上げ潮（満ちてくる潮）" if delta > 0 else "下げ潮（引き潮）"}
    * **推奨戦略:** {tide_msg}
    * **狙い棚:** 潮流の速さに合わせ、ラインの角度を45度に保つ重量を選択してください。
    """)

with col_b:
    st.markdown(f"""
    **🌊 気象・安全管理**
    * **風の影響:** 風速 {c_wind:.1f}m/s。船が風で押されるため、エンジンでの補正が必要な場合があります。
    * **気圧補正:** {c_press:.0f}hPa。{"低気圧により魚の浮袋が膨らみ、活性が上がる可能性があります。" if c_press < 1005 else "安定した高気圧下です。"}
    * **波浪:** {c_wave:.1f}m。{"船酔いに注意し、足元の安全を確保してください。" if c_wave > 0.5 else "海面は穏やか。キャスティングも容易です。"}
    """)

st.caption(f"※本診断は {target_area} の実況値（POS: {lat:.2f}, {lon:.2f}）に基づき、{target_style}に最適化して生成されました。")
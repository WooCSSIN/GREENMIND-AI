import streamlit as st
import plotly.graph_objects as go
import pandas as pd

def render_forecast_view(engine, sku_mapping, inventory_ctrl, logistics_ctrl):
    st.sidebar.subheader("Cấu hình Phân tích")
    selected_label = st.sidebar.selectbox(
        "Mã hàng hóa (SKU)", 
        options=list(sku_mapping.keys())
    )
    selected_sku = sku_mapping[selected_label]
    selected_name = selected_label.split(" | ")[1] if " | " in selected_label else "Sản phẩm"
    
    st.caption(f"Mã định danh SKU: {selected_sku} - {selected_name}")
    
    try:
        with st.spinner("Đang xử lý thuật toán tối ưu..."):
            results = engine.compare_models(selected_sku)
            future = engine.forecast_future(selected_sku, days=30)
    
        col1, col2, col3 = st.columns(3)
    
        if len(future['forecast_values']) > 0:
            tomorrow_stock = float(future['forecast_values'][0])
            if tomorrow_stock < 50:
                status, color = "Nguy cấp (Hết hàng)", "#dc3545"
            elif tomorrow_stock < 150:
                status, color = "Cảnh báo (Tồn thấp)", "#ffc107"
            else:
                status, color = "An toàn (Định mức tiêu chuẩn)", "#28a745"
        else:
            status, color = "Dữ liệu không khả dụng", "#6c757d"
    
        with col1:
            st.markdown(f"""
                <div class="status-card" style="background-color:{color};">
                    <div style="font-size: 0.8rem; text-transform: uppercase; opacity: 0.9;">Tình trạng kho dự kiến</div>
                    <div style="font-size: 1.2rem; margin-top: 5px;">{status}</div>
                    <div style="font-size: 0.9rem; margin-top: 8px; opacity: 0.8;">Dự báo ngày mai: {tomorrow_stock:,.0f} Đv</div>
                </div>
            """, unsafe_allow_html=True)
    
        with col2:
            st.metric("Công nghệ dự báo", results['champion'], help="Mô hình có chỉ số sai số huấn luyện thấp nhất.")
            st.caption("Dựa trên so sánh RMSE/MAE tự động")
    
        with col3:
            st.metric(
                label="Chỉ số Phát thải Tiết kiệm", 
                value=f"{results['green_impact']['annual_co2_kg']:,.1f} kg CO2",
                delta=f"{results['green_impact']['trees_equivalent']:,.0f} cây/năm"
            )
            st.caption("Dự toán tối ưu hóa nguồn lực chuỗi cung ứng.")
    
        st.divider()
        st.subheader("Diễn biến Tồn kho và Mô hình Dự báo (30 ngày)")
        hist_data = engine.get_product_data(selected_sku).tail(30).copy()
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=hist_data['timestamp'], y=hist_data['stock'],
            name="Dữ liệu Lịch sử", line=dict(color="#0d6efd", width=2)
        ))
        if len(future['forecast_values']) > 0:
            fig.add_trace(go.Scatter(
                x=future['forecast_dates'], y=future['forecast_values'],
                name=f"Dự báo Hệ thống ({future['model_used']})",
                line=dict(color="#fd7e14", width=2, dash='dash')
            ))
        fig.update_layout(
            template="plotly_white", 
            hovermode="x unified", 
            height=400,
            margin=dict(l=0, r=0, t=20, b=0),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig, use_container_width=True)

        st.divider()
        dcol1, dcol2 = st.columns([2, 1])
        
        with dcol1:
            st.subheader(" Hệ thống Hỗ trợ Ra quyết định (DSS)")
            st.markdown("Dựa trên phân tích sai số dự báo và thời gian chờ nhập hàng (Lead Time).")
            
            reco = inventory_ctrl.get_dss_recommendations(selected_sku)
            
            m1, m2, m3 = st.columns(3)
            m1.metric("Safety Stock Gợi ý", f"{reco['safety_stock_optimized']:,.0f} đv", help="Lượng tồn kho an toàn tối ưu tính theo sai số AI.")
            m2.metric("Điểm đặt hàng (ROP)", f"{reco['reorder_point']:,.0f} đv", help="Khi kho chạm mức này, hệ thống sẽ báo nhập hàng.")
            m3.metric("Nhu cầu Lead-time", f"{reco['lead_time_demand']:,.0f} đv")
            
            if st.button(" Tối ưu hóa tham số CSDL (Feedback Loop)", use_container_width=True):
                success, msg = inventory_ctrl.process_feedback_loop(selected_sku)
                if success:
                    st.success(msg)
                    st.balloons()
                else:
                    st.error(msg)
            
        with dcol2:
            st.subheader(" Logistics Link")
            st.markdown("Kết nối với mạng lưới vận chuyển nội địa.")
            if st.button("Kích hoạt Abivin vRoute Integration", use_container_width=True, type="primary"):
                success, msg = logistics_ctrl.send_to_vroute(selected_sku, reco['reorder_point'])
                if success:
                    st.success(msg)
                    st.toast("Abivin vRoute: Đang tối ưu lộ trình xe tải...")
                else:
                    st.error(msg)

        with st.expander("Báo cáo Chi tiết Hiệu năng Thuật toán"):
            battle_disp = results['battle_results'].copy()
            battle_disp.columns = ["Mô hình", "MAE", "RMSE"]
            st.dataframe(battle_disp.reset_index(drop=True), use_container_width=True)
            
    except Exception as e:
        st.error(f"Lỗi hệ thống trong quá trình phân tích: {str(e)}")

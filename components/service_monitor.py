import streamlit as st
import asyncio
from utils.service_monitor import monitor
import time
import pandas as pd

def render_service_status():
    """Render service monitoring dashboard"""
    st.markdown("""
    <style>
    .status-healthy {
        color: #28a745;
        font-weight: bold;
    }
    .status-unhealthy {
        color: #dc3545;
        font-weight: bold;
    }
    .status-unknown {
        color: #6c757d;
        font-weight: bold;
    }
    .metric-card {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #f8f9fa;
        margin-bottom: 1rem;
    }
    </style>
    """, unsafe_allow_html=True)

    st.header("🔍 Monitor de Servicios")

    # Overall system health
    overall_health = monitor.get_overall_health()
    health_color = {
        'healthy': 'status-healthy',
        'unhealthy': 'status-unhealthy',
        'unknown': 'status-unknown'
    }
    
    st.markdown(f"""
    ### Estado General del Sistema: 
    <span class="{health_color[overall_health]}">
        {overall_health.upper()}
    </span>
    """, unsafe_allow_html=True)

    # Update metrics
    asyncio.run(monitor.monitor_services())
    metrics = monitor.get_metrics()

    # Display service status
    col1, col2, col3 = st.columns(3)
    services = {
        'streamlit': ('Streamlit', '🌐', col1),
        'api': ('API', '🔌', col2),
        'webrtc': ('WebRTC', '📡', col3)
    }

    for service_id, (service_name, icon, col) in services.items():
        metric = metrics.get(service_id, {
            'status': 'unknown',
            'response_time': None,
            'last_check': None,
            'error': None
        })
        
        with col:
            st.markdown(f"""
            <div class="metric-card">
                <h4>{icon} {service_name}</h4>
                <p class="{health_color[metric['status']]}">
                    {metric['status'].upper()}
                </p>
                <p><small>Tiempo de respuesta: {
                    f"{metric['response_time']:.2f}ms" if metric['response_time'] else "N/A"
                }</small></p>
                <p><small>Última verificación: {
                    metric['last_check'].split('T')[1].split('.')[0] if metric['last_check'] else "N/A"
                }</small></p>
                {f"<p style='color: #dc3545'><small>Error: {metric['error']}</small></p>" if metric['error'] else ""}
            </div>
            """, unsafe_allow_html=True)

    # Show detailed metrics table
    st.subheader("📊 Métricas Detalladas")
    
    metrics_df = pd.DataFrame([
        {
            'Servicio': name,
            'Estado': data['status'],
            'Tiempo de Respuesta (ms)': f"{data['response_time']:.2f}" if data['response_time'] else "N/A",
            'Última Verificación': data['last_check'].split('T')[0] + " " + data['last_check'].split('T')[1].split('.')[0] if data['last_check'] else "N/A",
            'Error': data['error'] if data['error'] else "Ninguno"
        }
        for name, data in metrics.items()
    ])
    
    st.dataframe(metrics_df, use_container_width=True)

    # Auto-refresh
    time.sleep(5)
    st.experimental_rerun()

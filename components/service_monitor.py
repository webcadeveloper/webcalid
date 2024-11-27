import streamlit as st
import asyncio
from datetime import datetime
import pandas as pd
import time
from utils.service_monitor import monitor

def render_service_status():
    """Render service monitoring dashboard with enhanced error handling and real-time updates"""
    st.markdown("### 🔄 Monitor de Servicios en Tiempo Real")
    st.markdown("""
        Este panel muestra el estado actual de todos los servicios críticos del sistema.
        Se actualiza automáticamente cada 5 segundos.
    """)
    try:
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
        .status-warning {
            color: #ffc107;
            font-weight: bold;
        }
        .metric-card {
            padding: 1rem;
            border-radius: 0.5rem;
            background-color: #f8f9fa;
            margin-bottom: 1rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .service-details {
            font-size: 0.9rem;
            margin-top: 0.5rem;
        }
        .error-message {
            color: #dc3545;
            font-size: 0.9rem;
            margin-top: 0.5rem;
        }
        </style>
        """, unsafe_allow_html=True)

        # Update metrics
        asyncio.run(monitor.monitor_services())
        metrics = monitor.get_metrics()

        # Overall system health
        overall_health = monitor.get_overall_health()
        health_color = {
            'healthy': 'status-healthy',
            'unhealthy': 'status-unhealthy',
            'warning': 'status-warning',
            'unknown': 'status-unknown'
        }

        st.markdown(f"""
        ### Estado del Sistema
        <div class="metric-card">
            <h4>Estado General:</h4>
            <p class="{health_color[overall_health]}">
                {overall_health.upper()}
            </p>
            <p class="service-details">
                Última actualización: {datetime.now().strftime('%H:%M:%S')}
            </p>
        </div>
        """, unsafe_allow_html=True)

        # Display individual service status
        col1, col2, col3 = st.columns(3)
        services = {
            'streamlit': ('Streamlit Dashboard', '🌐', col1),
            'api': ('API REST', '🔌', col2),
            'webrtc': ('WebRTC Signaling', '📡', col3)
        }

        for service_id, (service_name, icon, col) in services.items():
            metric = metrics.get(service_id, {
                'status': 'unknown',
                'response_time': None,
                'last_check': None,
                'error': None
            })

            status_class = health_color.get(metric['status'], 'status-unknown')
            
            with col:
                st.markdown(f"""
                <div class="metric-card">
                    <h4>{icon} {service_name}</h4>
                    <p class="{status_class}">
                        {metric['status'].upper()}
                    </p>
                    <div class="service-details">
                        <p>Tiempo de respuesta: {
                            f"{metric['response_time']:.2f}ms" if metric['response_time'] else "N/A"
                        }</p>
                        <p>Última verificación: {
                            metric['last_check'].split('T')[1].split('.')[0] if metric['last_check'] else "N/A"
                        }</p>
                        {f'<p class="error-message">Error: {metric["error"]}</p>' if metric['error'] else ""}
                    </div>
                </div>
                """, unsafe_allow_html=True)

        # Detailed metrics table
        st.markdown("### 📊 Métricas Detalladas")
        
        try:
            metrics_df = pd.DataFrame([
                {
                    'Servicio': name,
                    'Estado': data['status'].upper(),
                    'Tiempo de Respuesta (ms)': f"{data['response_time']:.2f}" if data['response_time'] else "N/A",
                    'Última Verificación': data['last_check'].split('T')[0] + " " + data['last_check'].split('T')[1].split('.')[0] if data['last_check'] else "N/A",
                    'Error': data['error'] if data['error'] else "Ninguno"
                }
                for name, data in metrics.items()
            ])
            
            st.dataframe(
                metrics_df.style.apply(lambda x: ['background-color: #e2f0d9' if 'HEALTHY' in i else 
                                                'background-color: #fce4e4' if 'UNHEALTHY' in i else 
                                                'background-color: #fff2cc' for i in x], 
                                    axis=1,
                                    subset=['Estado']),
                use_container_width=True
            )
        except Exception as e:
            st.error(f"Error al generar tabla de métricas: {str(e)}")

        # Auto-refresh with error handling
        try:
            time.sleep(5)
            st.experimental_rerun()
        except Exception as e:
            st.warning(f"Error al actualizar automáticamente: {str(e)}")

    except Exception as e:
        st.error(f"Error en el monitor de servicios: {str(e)}")
        st.info("Intentando recuperar en la próxima actualización...")
        time.sleep(5)
        st.experimental_rerun()

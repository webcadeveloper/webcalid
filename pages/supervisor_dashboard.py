import streamlit as st
import sqlite3
from datetime import datetime, timedelta
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils.auth import check_role, logout
from components.service_monitor import render_service_status
from utils.service_monitor import monitor
import asyncio

class SupervisorDashboard:
    def __init__(self):
        self.conn = sqlite3.connect('cases_database.db')
        self.conn.row_factory = sqlite3.Row
        self.monitor = monitor

    async def update_metrics(self):
        """Update service metrics asynchronously"""
        try:
            await self.monitor.monitor_services()
            return self.monitor.get_metrics()
        except Exception as e:
            st.error(f"Error actualizando métricas: {str(e)}")
            return {}

    def render_dashboard(self):
        st.title("Dashboard del Supervisor")
        
        # Add monitoring section first
        st.subheader("🖥️ Estado de los Servicios")
        
        # Create metrics placeholder
        metrics_placeholder = st.empty()
        
        try:
            # Get initial metrics
            metrics = asyncio.run(self.update_metrics())
            overall_health = self.monitor.get_overall_health()
            
            # Display metrics in columns
            col1, col2, col3 = st.columns(3)
            
            with col1:
                status_color = {
                    'healthy': 'green',
                    'warning': 'orange',
                    'unhealthy': 'red',
                    'unknown': 'gray'
                }
                st.markdown(f"""
                    <div style='padding: 1rem; border-radius: 0.5rem; background-color: #f0f2f6;'>
                        <h3>Estado General</h3>
                        <p style='color: {status_color.get(overall_health, "gray")}; font-size: 1.2rem; font-weight: bold;'>
                            {overall_health.upper()}
                        </p>
                    </div>
                """, unsafe_allow_html=True)
            
            with col2:
                healthy_services = sum(1 for m in metrics.values() if m['status'] == 'healthy')
                st.markdown(f"""
                    <div style='padding: 1rem; border-radius: 0.5rem; background-color: #f0f2f6;'>
                        <h3>Servicios Saludables</h3>
                        <p style='color: {"green" if healthy_services == len(metrics) else "orange"}; font-size: 1.2rem; font-weight: bold;'>
                            {healthy_services}/{len(metrics)}
                        </p>
                    </div>
                """, unsafe_allow_html=True)
            
            with col3:
                response_times = [m['response_time'] for m in metrics.values() if m['response_time']]
                avg_response = sum(response_times) / len(response_times) if response_times else 0
                st.markdown(f"""
                    <div style='padding: 1rem; border-radius: 0.5rem; background-color: #f0f2f6;'>
                        <h3>Tiempo de Respuesta</h3>
                        <p style='color: blue; font-size: 1.2rem; font-weight: bold;'>
                            {avg_response:.2f}ms
                        </p>
                    </div>
                """, unsafe_allow_html=True)

            # Render detailed service status
            render_service_status()

        except Exception as e:
            st.error(f"Error al cargar el monitor de servicios: {str(e)}")

    def __del__(self):
        if hasattr(self, 'conn'):
            self.conn.close()

def page_render():
    if not check_role('supervisor'):
        return

    st.set_page_config(
        page_title="Dashboard del Supervisor",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    st.sidebar.title("Menú")
    if st.sidebar.button("Cerrar Sesión"):
        logout()
        st.rerun()

    try:
        dashboard = SupervisorDashboard()
        dashboard.render_dashboard()
    except Exception as e:
        st.error(f"Error al cargar el dashboard: {e}")

if __name__ == "__main__":
    page_render()

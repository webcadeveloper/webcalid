import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from utils.database import get_db_connection
from utils.auth_utils import check_role

class SupervisorAnalytics:
    def render(self):
        check_role('supervisor')
        st.title("Supervisor Dashboard")
        self._show_metrics()
        self._show_daily_activity()
        self._show_call_metrics()

    def _show_metrics(self):
        metrics = self._get_metrics()
        cols = st.columns(4)
        cols[0].metric("Total Búsquedas", metrics['total_searches'])
        cols[1].metric("Llamadas Exitosas", metrics['successful_calls'])
        cols[2].metric("Tasa de Éxito", f"{metrics['success_rate']}%")
        cols[3].metric("Tiempo Promedio", f"{metrics['avg_duration']}s")

    def _show_daily_activity(self):
        data = self._get_daily_activity()
        fig = px.line(data, x='date', y=['searches', 'calls'], title="Actividad Diaria")
        st.plotly_chart(fig)

    def _show_call_metrics(self):
        data = self._get_call_metrics()
        fig = go.Figure(data=[go.Pie(labels=data['status'], values=data['count'])])
        st.plotly_chart(fig)

    def _get_metrics(self):
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT 
                    COUNT(*) AS total_searches,
                    SUM(CASE WHEN call_status = 'successful' THEN 1 ELSE 0 END) AS successful_calls,
                    ROUND(SUM(CASE WHEN call_status = 'successful' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS success_rate,
                    ROUND(AVG(call_duration), 2) AS avg_duration
                FROM phone_calls
            """)
            return dict(zip(['total_searches', 'successful_calls', 'success_rate', 'avg_duration'], cur.fetchone()))

    def _get_daily_activity(self):
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT 
                    DATE(call_date) AS date,
                    COUNT(CASE WHEN call_status = 'initiated' THEN 1 END) AS searches,
                    COUNT(CASE WHEN call_status = 'successful' THEN 1 END) AS calls
                FROM phone_calls
                GROUP BY date
                ORDER BY date DESC
                LIMIT 30
            """)
            return pd.DataFrame(cur.fetchall(), columns=['date', 'searches', 'calls'])

    def _get_call_metrics(self):
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT 
                    call_status, 
                    COUNT(*) AS count
                FROM phone_calls
                GROUP BY call_status
            """)
            return {'status': [row[0] for row in cur.fetchall()], 'count': [row[1] for row in cur.fetchall()]}
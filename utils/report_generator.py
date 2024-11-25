import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from database import get_db_connection
from datetime import datetime
import io
from io import BytesIO
import base64

def page_render():
    if not st.session_state.get('user_id'):
        st.warning("Por favor inicie sesión")
        st.stop()
        return

class ReportGenerator:
    def __init__(self):
        self.conn = get_db_connection()

    def render(self):
        st.title("Generador de Reportes de Llamadas y Leads")

        report_type = st.selectbox(
            "Tipo de Reporte",
            ["Llamadas Realizadas", "Leads Generados", "Rendimiento de Agentes"]
        )

        date_range = st.date_input(
            "Rango de Fechas",
            [datetime.now().date(), datetime.now().date()]
        )

        if st.button("Generar"):
            self._generate_report(report_type, date_range)

    def _generate_report(self, report_type, dates):
        data = self._get_report_data(report_type, dates)

        if data.empty:
            st.warning("No hay datos para el período seleccionado")
            return

        # Generar gráfico
        fig = self._generate_chart(report_type, data)
        st.pyplot(fig)

        # Generar Excel
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            data.to_excel(writer, sheet_name='Report', index=False)

        st.download_button(
            "Descargar Reporte",
            buffer.getvalue(),
            f"reporte_{report_type}_{dates[0]}.xlsx",
            "application/vnd.ms-excel"
        )

    def _get_report_data(self, report_type, dates):
        queries = {
            "Llamadas Realizadas": """
                SELECT DATE(call_date) as fecha, COUNT(*) as total_llamadas
                FROM phone_calls 
                WHERE call_date BETWEEN %s AND %s
                GROUP BY DATE(call_date)
                ORDER BY fecha
            """,
            "Leads Generados": """
                SELECT DATE(lead_date) as fecha, COUNT(*) as total_leads
                FROM leads 
                WHERE lead_date BETWEEN %s AND %s
                GROUP BY DATE(lead_date)
                ORDER BY fecha
            """,
            "Rendimiento de Agentes": """
                SELECT u.username, COUNT(pc.id) as total_llamadas, COUNT(l.id) as total_leads
                FROM users u
                LEFT JOIN phone_calls pc ON u.id = pc.user_id AND pc.call_date BETWEEN %s AND %s
                LEFT JOIN leads l ON u.id = l.user_id AND l.lead_date BETWEEN %s AND %s
                GROUP BY u.username
                ORDER BY total_leads DESC
            """
        }

        query = queries.get(report_type)
        return pd.read_sql_query(query, self.conn, params=dates*2 if report_type == "Rendimiento de Agentes" else dates)

    def _generate_chart(self, report_type, data):
        plt.figure(figsize=(12, 6))
        if report_type in ["Llamadas Realizadas", "Leads Generados"]:
            plt.plot(data['fecha'], data['total_llamadas' if report_type == "Llamadas Realizadas" else 'total_leads'])
            plt.title(f'{report_type} por Día')
            plt.xlabel('Fecha')
            plt.ylabel('Cantidad')
            plt.xticks(rotation=45)
        else:  # Rendimiento de Agentes
            bar_width = 0.35
            index = range(len(data))
            plt.bar(index, data['total_llamadas'], bar_width, label='Llamadas')
            plt.bar([i + bar_width for i in index], data['total_leads'], bar_width, label='Leads')
            plt.title('Rendimiento de Agentes')
            plt.xlabel('Agentes')
            plt.ylabel('Cantidad')
            plt.xticks([i + bar_width/2 for i in index], data['username'], rotation=45)
            plt.legend()

        plt.tight_layout()
        return plt.gcf()

    def get_image_base64(self):
        buffer = BytesIO()
        plt.savefig(buffer, format='png')
        buffer.seek(0)
        image_png = buffer.getvalue()
        graph = base64.b64encode(image_png)
        graph = graph.decode('utf-8')
        buffer.close()
        return f"data:image/png;base64,{graph}"



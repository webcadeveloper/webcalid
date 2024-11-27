import streamlit as st
import sqlite3
from datetime import datetime, timedelta
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils.auth import check_role, logout
from components.service_monitor import render_service_status

class SupervisorDashboard:
    def __init__(self):
        self.conn = sqlite3.connect('cases_database.db')
        self.conn.row_factory = sqlite3.Row

    def get_pending_cases(self):
        query = """
        SELECT 
            c.id, c.number, c.status, c.first_name, c.last_name, c.a_number,
            c.court_address, c.court_phone, c.client_phone,
            c.created_at, u.username as operator
        FROM cases c
        JOIN users u ON c.created_by = u.id
        WHERE c.status = 'Positivo' 
        AND c.id NOT IN (SELECT case_id FROM case_approvals)
        ORDER BY c.created_at DESC
        """
        return pd.read_sql_query(query, self.conn)

    def approve_case(self, case_id, supervisor_id):
        cursor = self.conn.cursor()
        try:
            current_date = datetime.now()
            period_start = current_date.replace(day=1 if current_date.day > 15 else 16)
            period_end = (period_start + timedelta(days=14))
            approval_number = f"AP{current_date.strftime('%Y%m')}-{case_id:04d}"

            cursor.execute("""
                INSERT INTO case_approvals (
                    case_id, approved_by, approval_number, 
                    period_start, period_end, approval_status
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (case_id, supervisor_id, approval_number, period_start, period_end, 'APPROVED'))

            cursor.execute("""
                INSERT INTO notifications (user_id, case_id, message)
                SELECT created_by, id, 
                       'Tu caso ' || number || ' ha sido aprobado con el número ' || ?
                FROM cases WHERE id = ?
            """, (approval_number, case_id))

            self.conn.commit()
            return True
        except Exception as e:
            self.conn.rollback()
            st.error(f"Error al aprobar caso: {e}")
            return False

    def get_operator_performance(self):
        query = """
        SELECT 
            u.username as operator,
            COUNT(c.id) as total_cases,
            SUM(CASE WHEN c.status = 'Positivo' THEN 1 ELSE 0 END) as positive_cases,
            COUNT(ca.id) as approved_cases
        FROM users u
        LEFT JOIN cases c ON u.id = c.created_by
        LEFT JOIN case_approvals ca ON c.id = ca.case_id
        WHERE u.role = 'operator'
        GROUP BY u.username
        """
        return pd.read_sql_query(query, self.conn)

    def get_case_statistics(self):
        query = """
        SELECT 
            strftime('%Y-%m', created_at) as month,
            COUNT(*) as total_cases,
            SUM(CASE WHEN status = 'Positivo' THEN 1 ELSE 0 END) as positive_cases
        FROM cases
        GROUP BY strftime('%Y-%m', created_at)
        ORDER BY month DESC
        LIMIT 12
        """
        return pd.read_sql_query(query, self.conn)

    def get_cases_by_operator(self):
        query = """
        SELECT 
            u.username as operator,
            c.id,
            c.number,
            c.status,
            c.first_name,
            c.last_name,
            c.a_number,
            c.created_at,
            c.court_address,
            c.court_phone,
            c.client_phone,
            CASE 
                WHEN ca.approval_number IS NOT NULL 
                THEN ca.approval_number 
                ELSE 'Pendiente' 
            END as approval_status
        FROM users u
        LEFT JOIN cases c ON u.id = c.created_by
        LEFT JOIN case_approvals ca ON c.id = ca.case_id
        WHERE u.role = 'operator'
        ORDER BY u.username, c.created_at DESC
        """
        return pd.read_sql_query(query, self.conn)

    def render_dashboard(self):
        st.title("Dashboard del Supervisor")

        st.markdown("""
        <style>
        .metric-card {
            background-color: #f0f2f6;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        .success-metric {
            color: #28a745;
            font-weight: bold;
            font-size: 24px;
        }
        .warning-metric {
            color: #ffc107;
            font-weight: bold;
            font-size: 24px;
        }
        .info-metric {
            color: #17a2b8;
            font-weight: bold;
            font-size: 24px;
        }
        .stTabs [data-baseweb="tab-list"] {
            gap: 24px;
        }
        .stTabs [data-baseweb="tab"] {
            padding-left: 20px;
            padding-right: 20px;
        }
        </style>
        """, unsafe_allow_html=True)

        # Métricas principales
        col1, col2, col3 = st.columns(3)

        with col1:
            pending_cases = self.get_pending_cases()
            pending_count = len(pending_cases)
            st.markdown(f"""
            <div class="metric-card">
                <h3>Casos Pendientes</h3>
                <p class="warning-metric">{pending_count}</p>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            approved_today = pd.read_sql_query("""
                SELECT COUNT(*) as count 
                FROM case_approvals 
                WHERE date(approval_date) = date('now')
            """, self.conn).iloc[0]['count']
            st.markdown(f"""
            <div class="metric-card">
                <h3>Aprobados Hoy</h3>
                <p class="success-metric">{approved_today}</p>
            </div>
            """, unsafe_allow_html=True)

        with col3:
            total_approved = pd.read_sql_query("""
                SELECT COUNT(*) as count FROM case_approvals
            """, self.conn).iloc[0]['count']
            st.markdown(f"""
            <div class="metric-card">
                <h3>Total Aprobados</h3>
                <p class="info-metric">{total_approved}</p>
            </div>
            """, unsafe_allow_html=True)

        # Pestañas para diferentes secciones
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📊 Estadísticas", 
            "📝 Casos Pendientes", 
            "👥 Rendimiento de Operadores",
            "📋 Casos por Operador",
            "🔍 Monitor de Servicios"
        ])

        with tab1:
            st.subheader("Estadísticas de Casos")
            stats = self.get_case_statistics()

            if not stats.empty:
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=stats['month'],
                    y=stats['total_cases'],
                    name='Total Casos',
                    line=dict(color='#17a2b8', width=3)
                ))
                fig.add_trace(go.Scatter(
                    x=stats['month'],
                    y=stats['positive_cases'],
                    name='Casos Positivos',
                    line=dict(color='#28a745', width=3)
                ))
                fig.update_layout(
                    title='Evolución de Casos por Mes',
                    xaxis_title='Mes',
                    yaxis_title='Número de Casos',
                    hovermode='x unified',
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)'
                )
                st.plotly_chart(fig, use_container_width=True)

                stats['success_rate'] = (stats['positive_cases'] / stats['total_cases'] * 100).round(2)
                col1, col2 = st.columns(2)
                with col1:
                    current_month_rate = stats.iloc[0]['success_rate']
                    st.metric("Tasa de Éxito (Mes Actual)", f"{current_month_rate}%")
                with col2:
                    avg_rate = stats['success_rate'].mean()
                    st.metric("Tasa de Éxito Promedio", f"{avg_rate:.2f}%")

        with tab2:
            st.subheader("Casos Pendientes de Aprobación")
            if not pending_cases.empty:
                for _, case in pending_cases.iterrows():
                    with st.expander(f"📁 {case['first_name']} {case['last_name']} - A{case['a_number']}"):
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.write(f"**Número de caso:** {case['number']}")
                            st.write(f"**Operador:** {case['operator']}")
                            st.write(f"**Fecha de creación:** {case['created_at']}")
                            st.write(f"**Dirección de la Corte:** {case['court_address']}")
                            st.write(f"**Teléfono de la Corte:** {case['court_phone']}")
                            if case['client_phone']:
                                st.write(f"**Teléfono del Cliente:** {case['client_phone']}")
                        with col2:
                            if st.button("✅ Aprobar", key=f"approve_{case['id']}"):
                                if self.approve_case(case['id'], st.session_state.user_id):
                                    st.success("Caso aprobado exitosamente")
                                    st.rerun()
            else:
                st.info("No hay casos pendientes de aprobación")

        with tab3:
            st.subheader("Rendimiento de Operadores")
            performance_data = self.get_operator_performance()

            if not performance_data.empty:
                performance_data['success_rate'] = (performance_data['positive_cases'] / 
                                               performance_data['total_cases'] * 100).round(2)
                performance_data['approval_rate'] = (performance_data['approved_cases'] / 
                                                performance_data['positive_cases'] * 100).round(2)

                st.dataframe(
                    performance_data.style.format({
                        'success_rate': '{:.2f}%',
                        'approval_rate': '{:.2f}%'
                    }).background_gradient(cmap='YlGn', subset=['success_rate', 'approval_rate']),
                    use_container_width=True
                )

                fig = px.bar(
                    performance_data,
                    x='operator',
                    y=['total_cases', 'positive_cases', 'approved_cases'],
                    title='Comparación de Casos por Operador',
                    barmode='group',
                    color_discrete_sequence=['#17a2b8', '#28a745', '#ffc107']
                )
                fig.update_layout(
                    xaxis_title='Operador',
                    yaxis_title='Número de Casos',
                    legend_title='Tipo de Caso',
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)'
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No hay datos de rendimiento disponibles")

        with tab4:
            st.subheader("Casos por Operador")
            cases_by_operator = self.get_cases_by_operator()

            if not cases_by_operator.empty:
                operators = cases_by_operator['operator'].unique()
                selected_operator = st.selectbox(
                    "Seleccionar Operador",
                    options=operators
                )
                operator_cases = cases_by_operator[
                    cases_by_operator['operator'] == selected_operator
                ]

                col1, col2, col3 = st.columns(3)
                with col1:
                    total_cases = len(operator_cases)
                    st.markdown(f"""
                    <div class="metric-card">
                        <h3>Total de Casos</h3>
                        <p class="info-metric">{total_cases}</p>
                    </div>
                    """, unsafe_allow_html=True)

                with col2:
                    approved_cases = len(operator_cases[
                        operator_cases['approval_status'] != 'Pendiente'
                    ])
                    st.markdown(f"""
                    <div class="metric-card">
                        <h3>Casos Aprobados</h3>
                        <p class="success-metric">{approved_cases}</p>
                    </div>
                    """, unsafe_allow_html=True)

                with col3:
                    pending_cases = len(operator_cases[
                        operator_cases['approval_status'] == 'Pendiente'
                    ])
                    st.markdown(f"""
                    <div class="metric-card">
                        <h3>Casos Pendientes</h3>
                        <p class="warning-metric">{pending_cases}</p>
                    </div>
                    """, unsafe_allow_html=True)

                st.subheader(f"Lista de Casos - {selected_operator}")

                status_filter = st.multiselect(
                    "Filtrar por Estado",
                    options=operator_cases['status'].unique(),
                    default=operator_cases['status'].unique()
                )

                filtered_cases = operator_cases[
                    operator_cases['status'].isin(status_filter)
                ]

                for _, case in filtered_cases.iterrows():
                    with st.expander(f"📁 {case['first_name']} {case['last_name']} - A{case['a_number']}"):
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.write(f"**Número de caso:** {case['number']}")
                            st.write(f"**Estado:** {case['status']}")
                            st.write(f"**Fecha de creación:** {case['created_at']}")
                            st.write(f"**Dirección de la Corte:** {case['court_address']}")
                            st.write(f"**Teléfono de la Corte:** {case['court_phone']}")
                            if case['client_phone']:
                                st.write(f"**Teléfono del Cliente:** {case['client_phone']}")
                        with col2:
                            st.write("**Estado de Aprobación:**")
                            if case['approval_status'] == 'Pendiente':
                                st.warning("⏳ Pendiente")
                                if case['status'] == 'Positivo':
                                    if st.button("✅ Aprobar", key=f"approve_{case['id']}"):
                                        if self.approve_case(case['id'], st.session_state.user_id):
                                            st.success("Caso aprobado exitosamente")
                                            st.rerun()
                            else:
                                st.success(f"✅ {case['approval_status']}")
            else:
                st.info("No hay casos registrados")

        with tab5:
            render_service_status()

    def __del__(self):
        if hasattr(self, 'conn'):
            self.conn.close()

def page_render():
    if not check_role('supervisor'):
        return

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
    st.set_page_config(page_title="Dashboard del Supervisor", page_icon="📊", layout="wide")
    page_render()

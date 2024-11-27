import streamlit as st
import sqlite3
from datetime import datetime

def get_db_connection():
    conn = sqlite3.connect('cases_database.db')
    conn.row_factory = sqlite3.Row
    return conn

def update_case(case_id, **updates):
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        update_fields = ', '.join([f"{k} = ?" for k in updates.keys()])
        update_values = list(updates.values())

        cursor.execute(f"""
            UPDATE cases 
            SET {update_fields}
            WHERE id = ? AND created_by = ?
        """, (*update_values, case_id, st.session_state.user_id))

        conn.commit()
        return True
    except sqlite3.Error as e:
        st.error(f"Error al actualizar el caso: {e}")
        return False
    finally:
        conn.close()

class CaseRecordsManagement:
    def __init__(self):
        pass
        
    def run(self):
        if 'user_id' not in st.session_state:
            st.error("Por favor, inicie sesión para acceder")
            st.stop()
            return
            
        self.render_dashboard()
            
    def render_dashboard(self):
        st.title("Gestión de Casos")
        
        # Verificar autenticación antes de proceder
        if not st.session_state.get('user_id'):
            st.error("Usuario no autenticado")
            st.stop()
            return

    # Aplicar estilos modernos
    st.markdown("""
    <style>
    /* Estilos generales */
    .main {
        padding: 2rem;
        max-width: 1200px;
        margin: 0 auto;
    }

    /* Variables de color */
    :root {
        --primary-color: #2E3B55;
        --secondary-color: #4CAF50;
        --accent-color: #FFB74D;
        --background-color: #F5F7FA;
        --text-color: #333333;
        --border-color: #E0E0E0;
    }

    /* Estilos de tarjetas */
    .case-card {
        background: white;
        border-radius: 10px;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
        padding: 1.5rem;
        margin: 1rem 0;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }

    .case-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.15);
    }

    /* Estilos para campos de formulario */
    .stTextInput > div > div {
        background-color: white;
        border-radius: 5px;
        border: 1px solid var(--border-color);
        padding: 0.5rem;
    }

    .stTextInput > div > div:focus-within {
        border-color: var(--primary-color);
        box-shadow: 0 0 0 2px rgba(46, 59, 85, 0.1);
    }

    /* Estilos para botones */
    .stButton > button {
        background-color: var(--primary-color) !important;
        color: white !important;
        border-radius: 5px !important;
        padding: 0.5rem 1.5rem !important;
        border: none !important;
        transition: background-color 0.2s ease !important;
    }

    .stButton > button:hover {
        background-color: #3E4E6E !important;
        border: none !important;
    }

    /* Estilos para el contenedor de búsqueda */
    .search-container {
        background: white;
        border-radius: 10px;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
        padding: 1rem;
        margin: 1rem 0;
    }

    .search-button {
        display: inline-block;
        padding: 0.5rem 1rem;
        background-color: var(--primary-color);
        color: white;
        text-decoration: none;
        border-radius: 5px;
        margin: 0.5rem 0;
        text-align: center;
    }

    .search-button:hover {
        background-color: #3E4E6E;
    }

    /* Estilos para campos requeridos */
    .required-field::after {
        content: " *";
        color: #FF5252;
        font-weight: bold;
    }

    /* Estilos para expansores */
    .streamlit-expanderHeader {
        background-color: var(--background-color);
        border-radius: 5px;
        padding: 0.5rem 1rem;
        font-weight: 500;
    }

    /* Estilos para títulos */
    h1, h2, h3 {
        color: var(--primary-color);
        margin-bottom: 1rem;
    }

    /* Estilos para mensajes */
    .success-message {
        background-color: #4CAF50;
        color: white;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }

    .error-message {
        background-color: #FF5252;
        color: white;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    </style>
    """, unsafe_allow_html=True)

    st.title("Gestión de Casos")

    # Sección de búsqueda
    st.markdown("### 🔍 Herramientas de Búsqueda")

    with st.container():
        st.markdown("""
        <div class="search-container">
            <h4>Enlaces de Búsqueda</h4>
            <div style="display: flex; gap: 1rem; flex-wrap: wrap;">
                <a href="https://www.whitepages.com/" target="_blank" class="search-button">
                    🌐 WhitePages
                </a>
                <a href="https://www.411.com/" target="_blank" class="search-button">
                    🔍 411.com
                </a>
                <a href="https://www.anywho.com/" target="_blank" class="search-button">
                    📱 AnyWho
                </a>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Obtener y mostrar casos
    conn = get_db_connection()
    cur = conn.cursor()

    if st.session_state.get('user_id'):
        cur.execute("""
            SELECT id, number, status, first_name, last_name, a_number, 
                   court_address, court_phone, client_phone, other_client_phone, 
                   client_address, client_email 
            FROM cases 
            WHERE created_by = %s 
            ORDER BY created_at DESC
        """, (st.session_state.user_id,))
    else:
        st.error("Usuario no autenticado")
        st.stop()
        return

    cases = cur.fetchall()

    st.markdown("### 📁 Mis Casos")

    if not cases:
        st.info("📭 No hay casos registrados")
    else:
        for case in cases:
            with st.expander(f"📋 {case['first_name']} {case['last_name']} - A{case['a_number']}"):
                col1, col2 = st.columns([2, 1])

                with col1:
                    st.markdown("#### Información del Caso")
                    new_values = {
                        'number': st.text_input("Número de caso *", value=case['number'], key=f"num_{case['id']}"),
                        'status': st.selectbox("Estado del caso *", ["Positivo", "Negativo"], 
                                             index=0 if case['status'] == "Positivo" else 1, 
                                             key=f"status_{case['id']}"),
                        'first_name': st.text_input("Nombre *", value=case['first_name'], key=f"fname_{case['id']}"),
                        'last_name': st.text_input("Apellido *", value=case['last_name'], key=f"lname_{case['id']}"),
                        'a_number': st.text_input("A-number (9 dígitos) *", value=case['a_number'], key=f"anum_{case['id']}"),
                        'court_address': st.text_input("Dirección de la Corte *", value=case['court_address'], key=f"cadd_{case['id']}"),
                        'court_phone': st.text_input("Teléfono de la Corte *", value=case['court_phone'], key=f"cphone_{case['id']}"),
                        'client_phone': st.text_input("Teléfono del Cliente", value=case['client_phone'], key=f"clphone_{case['id']}"),
                        'other_client_phone': st.text_input("Otro teléfono", value=case['other_client_phone'], key=f"oclphone_{case['id']}"),
                        'client_address': st.text_input("Dirección del Cliente", value=case['client_address'], key=f"cladd_{case['id']}"),
                        'client_email': st.text_input("Email del Cliente", value=case['client_email'], key=f"clemail_{case['id']}")
                    }

                with col2:
                    st.markdown("<br>" * 5, unsafe_allow_html=True)
                    if st.button("💾 Guardar Cambios", key=f"save_{case['id']}"):
                        required_fields = {
                            'Número de caso': new_values['number'],
                            'Nombre': new_values['first_name'],
                            'Apellido': new_values['last_name'],
                            'A-number': new_values['a_number'],
                            'Dirección de la Corte': new_values['court_address'],
                            'Teléfono de la Corte': new_values['court_phone']
                        }

                        missing_fields = [field for field, value in required_fields.items() if not value]

                        if missing_fields:
                            st.error(f"❌ Campos requeridos faltantes: {', '.join(missing_fields)}")
                        elif not new_values['a_number'].isdigit() or len(new_values['a_number']) != 9:
                            st.error("❌ El A-number debe contener exactamente 9 dígitos")
                        else:
                            if update_case(case['id'], **new_values):
                                st.success("✅ Caso actualizado correctamente")
                                st.rerun()

    cur.close()
    conn.close()

if __name__ == "__main__":
    st.set_page_config(
        page_title="Gestión de Casos",
        page_icon="📁",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    page_render()
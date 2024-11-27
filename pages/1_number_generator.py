import streamlit as st
import sqlite3
import requests
from bs4 import BeautifulSoup
import time

# Clase para interactuar con EOIR
class EOIRScraper:
    BASE_URL = "https://acis.eoir.justice.gov/en/"

    def search(self, number):
        response = requests.get(self.BASE_URL, params={'caseNumber': number})

        if response.status_code == 200:
            if "No case found" in response.text:
                return {'status': 'not_found'}
            else:
                data = self.extract_case_info(response.text)
                return {'status': 'success', 'data': data}
        else:
            return {'status': 'error', 'error': response.text}

    def extract_case_info(self, html):
        soup = BeautifulSoup(html, 'html.parser')
        a_number_element = soup.select_one('div.case-number')
        status_element = soup.select_one('div.case-status')

        case_info = {
            'a_number': a_number_element.text.strip() if a_number_element else "No encontrado",
            'status': status_element.text.strip() if status_element else "No encontrado",
        }

        return case_info

# Clase generadora de números
class NumberGenerator:
    def __init__(self):
        self.current_prefix = 244206

    def generate_number(self):
        new_number = str(self.current_prefix * 1000 + len(st.session_state.generated_numbers)).zfill(9)
        self.current_prefix += 1
        return new_number

# Función para conectar a la base de datos SQLite
def get_db_connection():
    conn = sqlite3.connect('/home/runner/SmartDashboardManager/eoir_scraper/database.db')
    conn.row_factory = sqlite3.Row
    return conn

# Función para guardar los datos en la base de datos
def save_to_db(case_number, case_status, is_positive, first_name, last_name, a_number, court_address, court_phone, client_phone, other_client_phone, client_address, client_email):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Insertar los datos del caso en la tabla 'cases'
    cursor.execute('''
    INSERT INTO cases (number, status, is_positive, first_name, last_name, a_number, court_address, court_phone, client_phone, other_client_phone, client_address, client_email)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (case_number, case_status, is_positive, first_name, last_name, a_number, court_address, court_phone, client_phone, other_client_phone, client_address, client_email))

    conn.commit()
    conn.close()

# Función para inicializar el estado de la sesión
def initialize_session_state():
    if 'generated_numbers' not in st.session_state:
        st.session_state.generated_numbers = []
    if 'search_history' not in st.session_state:
        st.session_state.search_history = []
    if 'number_generator' not in st.session_state:
        st.session_state.number_generator = NumberGenerator()
    if 'search_in_progress' not in st.session_state:
        st.session_state.search_in_progress = False
    if 'eoir_scraper' not in st.session_state:
        st.session_state.eoir_scraper = EOIRScraper()

# Función para realizar la búsqueda del número
def search_number(number, report_placeholder):
    report_placeholder.info(f"Buscando número: {number}")

    eoir_result = st.session_state.eoir_scraper.sync_search(number)

    if eoir_result['status'] == 'success':
        report_placeholder.success("¡Caso encontrado en EOIR!")
        case_info = eoir_result['data']
        case_status = case_info.get('status', '').lower()
        is_positive = "positivo" in case_status or "en proceso" in case_status
        
        # Display detailed case information
        with report_placeholder.expander("Detalles del Caso"):
            st.write("Información del Caso:")
            for key, value in case_info.items():
                st.write(f"{key.replace('_', ' ').title()}: {value}")
                
        return {
            'number': number,
            'eoir_found': True,
            'is_positive': is_positive,
            'eoir_data': case_info
        }
    elif eoir_result['status'] == 'not_found':
        report_placeholder.info("No se encontró el caso en EOIR")
        return {'number': number, 'eoir_found': False, 'is_positive': False}
    else:
        report_placeholder.error(f"Error al buscar en EOIR: {eoir_result.get('error', 'Error desconocido')}")
        return {'number': number, 'eoir_found': False, 'is_positive': False}

# Función para cargar el formulario de registro
def render_form():
    st.subheader("Formulario de Registro de Caso")

    # Entradas del formulario
    case_number = st.text_input("Número de caso:")
    case_status = st.selectbox("Estado del caso:", ["Positivo", "Negativo"])
    first_name = st.text_input("Nombre")
    last_name = st.text_input("Apellido")
    a_number = st.text_input("A-number (9 dígitos)")
    court_address = st.text_input("Dirección de la Corte")
    court_phone = st.text_input("Teléfono de la Corte")
    client_phone = st.text_input("Teléfono del Cliente")
    other_client_phone = st.text_input("Otro teléfono del Cliente")
    client_address = st.text_input("Dirección del Cliente")
    client_email = st.text_input("Email del Cliente")

    # Validación: Los campos obligatorios
    if st.button("Guardar Caso"):
        if case_number and case_status and first_name and last_name and a_number and court_address and court_phone and client_phone:
            is_positive = case_status == "Positivo"
            save_to_db(case_number, case_status, is_positive, first_name, last_name, a_number, court_address, court_phone, client_phone, other_client_phone, client_address, client_email)
            st.success(f"El caso {case_number} ha sido guardado con éxito.")
        else:
            st.error("Por favor, ingrese todos los datos obligatorios.")

# Función para renderizar el historial de búsqueda
def render_search_history():
    if st.session_state.search_history:
        st.markdown("<h3>Historial de Búsquedas</h3>", unsafe_allow_html=True)
        for item in reversed(st.session_state.search_history):
            status_text = "Positivo" if item.get('is_positive') else "Negativo"
            st.markdown(f"<div class='number-item'>{item['number']} - {status_text}</div>", unsafe_allow_html=True)

# Función para renderizar la página principal
def page_render():
    initialize_session_state()

    st.title("Generador de Números y Registro de Casos")

    # Mostrar los números generados previamente
    current_number = st.session_state.generated_numbers[-1] if st.session_state.generated_numbers else "000000000"
    st.markdown(f'<div class="number-display">{current_number}</div>', unsafe_allow_html=True)

    # Botón para generar nuevos números
    if st.button("Generar Nuevo Número"):
        new_number = st.session_state.number_generator.generate_number()
        st.session_state.generated_numbers.append(new_number)
        st.success(f"Nuevo número generado: {new_number}")

    col1, col2 = st.columns(2)

    report_placeholder = st.empty()

    with col1:
        if st.button("Iniciar Búsqueda Automática"):
            st.session_state.search_in_progress = True

    with col2:
        if st.button("Detener Búsqueda"):
            st.session_state.search_in_progress = False

    st.subheader("Buscar número específico")
    specific_number = st.text_input("Ingrese el número a buscar:")
    if st.button("Buscar"):
        if specific_number:
            search_result = search_number(specific_number, report_placeholder)
            st.session_state.search_history.append(search_result)
            save_to_db(specific_number, search_result['eoir_data']['status'], search_result['is_positive'])
        else:
            st.error("Por favor, ingrese un número para buscar.")

    if st.session_state.search_in_progress:
        while st.session_state.search_in_progress:
            new_number = st.session_state.number_generator.generate_number()
            st.session_state.generated_numbers.append(new_number)
            search_result = search_number(new_number, report_placeholder)
            st.session_state.search_history.append(search_result)

            if search_result['eoir_found']:
                st.session_state.search_in_progress = False
                break

            time.sleep(1)

    render_search_history()

    # Agregar Iframe de EOIR
    st.subheader("Página EOIR")
    st.markdown('<iframe src="https://acis.eoir.justice.gov/en/" width="100%" height="500px"></iframe>', unsafe_allow_html=True)

    # Mostrar formulario de registro
    render_form()

if __name__ == "__main__":
    st.set_page_config(page_title="Generador de Números", page_icon="🔢", layout="wide")
    page_render()

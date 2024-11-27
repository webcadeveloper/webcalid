import streamlit as st
import sqlite3
import requests
from bs4 import BeautifulSoup
import time
import hashlib
from functools import wraps

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
    conn = sqlite3.connect('cases_database.db')
    conn.row_factory = sqlite3.Row
    return conn

def require_auth(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if 'user_id' not in st.session_state:
            st.error("Por favor, inicie sesión para acceder")
            return None
        return func(*args, **kwargs)
    return wrapper

# Función para guardar los datos en la base de datos
def save_to_db(case_number, case_status, first_name, last_name, a_number, 
               court_address, court_phone, client_phone=None, other_client_phone=None, 
               client_address=None, client_email=None):
    if 'user_id' not in st.session_state:
        st.error("Por favor, inicie sesión para guardar casos")
        return False

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        is_positive = case_status == "Positivo"
        cursor.execute('''
        INSERT INTO cases (
            number, status, is_positive, first_name, last_name, a_number,
            court_address, court_phone, client_phone, other_client_phone,
            client_address, client_email, created_by
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (case_number, case_status, is_positive, first_name, last_name, 
              a_number, court_address, court_phone, client_phone, 
              other_client_phone, client_address, client_email,
              st.session_state.user_id))

        conn.commit()
        return True
    except sqlite3.Error as e:
        st.error(f"Error en la base de datos: {e}")
        return False
    finally:
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

    eoir_result = st.session_state.eoir_scraper.search(number)

    if eoir_result['status'] == 'success':
        report_placeholder.success("¡Caso encontrado en EOIR!")
        case_status = eoir_result['data']['status'].lower()
        is_positive = "positivo" in case_status or "en proceso" in case_status
        return {'number': number, 'eoir_found': True, 'is_positive': is_positive, 'eoir_data': eoir_result['data']}
    elif eoir_result['status'] == 'not_found':
        report_placeholder.info("No se encontró el caso en EOIR")
        return {'number': number, 'eoir_found': False, 'is_positive': False}
    else:
        report_placeholder.error(f"Error al buscar en EOIR: {eoir_result.get('error', 'Error desconocido')}")
        return {'number': number, 'eoir_found': False, 'is_positive': False}

def login_form():
    st.subheader("Iniciar Sesión")
    username = st.text_input("Usuario")
    password = st.text_input("Contraseña", type="password")

    if st.button("Ingresar"):
        if username and password:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                'SELECT id, password_hash FROM users WHERE username = ?', 
                (username,)
            )
            user = cursor.fetchone()
            conn.close()

            if user and user['password_hash'] == hashlib.sha256(password.encode()).hexdigest():
                st.session_state.user_id = user['id']
                st.success("¡Inicio de sesión exitoso!")
                st.rerun()
            else:
                st.error("Usuario o contraseña inválidos")

# Función para cargar el formulario de registro
@require_auth
def render_form():
    st.subheader("Formulario de Registro de Caso")

    # Campos obligatorios
    st.markdown("### Campos Obligatorios")
    case_number = st.text_input("Número de caso *")
    case_status = st.selectbox("Estado del caso *", ["Positivo", "Negativo"])
    first_name = st.text_input("Nombre *")
    last_name = st.text_input("Apellido *")
    a_number = st.text_input("A-number (9 dígitos) *")
    court_address = st.text_input("Dirección de la Corte *")
    court_phone = st.text_input("Teléfono de la Corte *")

    # Campos opcionales
    st.markdown("### Campos Opcionales")
    client_phone = st.text_input("Teléfono del Cliente")
    other_client_phone = st.text_input("Otro teléfono del Cliente")
    client_address = st.text_input("Dirección del Cliente")
    client_email = st.text_input("Email del Cliente")

    if st.button("Guardar Caso"):
        # Verificar solo los campos obligatorios
        if all([case_number, case_status, first_name, last_name, 
                a_number, court_address, court_phone]):

            # Validar formato del A-number
            if len(a_number) != 9 or not a_number.isdigit():
                st.error("El A-number debe contener exactamente 9 dígitos")
                return

            if save_to_db(case_number, case_status, first_name, last_name, 
                         a_number, court_address, court_phone, client_phone,
                         other_client_phone, client_address, client_email):
                st.success(f"El caso {case_number} ha sido guardado con éxito.")
        else:
            st.error("Por favor, complete todos los campos obligatorios (marcados con *)")

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

    if 'user_id' not in st.session_state:
        login_form()
    else:
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
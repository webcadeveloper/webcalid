import streamlit as st
import sqlite3

# Función para obtener los casos desde la base de datos
def get_all_cases_from_db():
    conn = sqlite3.connect('/home/runner/SmartDashboardManager/eoir_scraper/database.db')
    cursor = conn.cursor()

    # Seleccionar todos los casos de la tabla 'users'
    cursor.execute('SELECT * FROM users')
    cases = cursor.fetchall()

    conn.close()
    return cases

# Función para guardar un caso
def save_case_to_db(first_name, last_name, a_number, court_address, phone_number, address=None, email=None, others=None):
    conn = sqlite3.connect('/home/runner/SmartDashboardManager/eoir_scraper/database.db')
    cursor = conn.cursor()

    # Verificar si ya existe un caso con el mismo 'a_number'
    cursor.execute('SELECT id FROM users WHERE a_number = ?', (a_number,))
    existing_user = cursor.fetchone()

    if existing_user:
        st.error(f"Ya existe un caso con el número A: {a_number}. No se puede crear otro.")
    else:
        # Insertar un nuevo caso en la base de datos
        cursor.execute('''
        INSERT INTO users (first_name, last_name, a_number, court_address, phone_number, address, email, others)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (first_name, last_name, a_number, court_address, phone_number, address, email, others))

        conn.commit()
        st.success(f"Nuevo caso creado para: {first_name} {last_name} con A-number: {a_number}")

    conn.close()

# Página de Streamlit para capturar datos del caso y mostrar casos registrados
def page_render():
    st.title("Registrar Nuevo Caso")

    # Formulario de entrada para datos del caso
    first_name = st.text_input("Nombre")
    last_name = st.text_input("Apellido")
    a_number = st.text_input("A-Number (9 dígitos)")
    court_address = st.text_input("Dirección de la Corte")
    phone_number = st.text_input("Número de Teléfono")
    address = st.text_input("Dirección (Opcional)")
    email = st.text_input("Correo Electrónico (Opcional)")
    others = st.text_area("Otros (Opcional)")

    # Botón para guardar el caso
    if st.button("Guardar Caso"):
        if first_name and last_name and a_number and court_address and phone_number:
            # Llamada a la función para guardar los datos
            save_case_to_db(first_name, last_name, a_number, court_address, phone_number, address, email, others)
        else:
            st.error("Por favor, ingrese todos los datos requeridos.")

    # Mostrar todos los casos registrados
    st.subheader("Casos Registrados")
    cases = get_all_cases_from_db()

    if cases:
        # Mostrar cada caso en un formato legible
        for case in cases:
            case_id, first_name, last_name, a_number, court_address, phone_number, created_at, address, email, others = case
            st.write(f"**ID del Caso:** {case_id}")
            st.write(f"**Nombre:** {first_name} {last_name}")
            st.write(f"**A-Number:** {a_number}")
            st.write(f"**Dirección de la Corte:** {court_address}")
            st.write(f"**Número de Teléfono de la Corte:** {phone_number}")
            st.write(f"**Dirección del Usuario:** {address or 'No disponible'}")
            st.write(f"**Correo Electrónico:** {email or 'No disponible'}")
            st.write(f"**Otros:** {others or 'No disponible'}")
            st.write("---")
    else:
        st.write("No se han encontrado casos registrados.")

if __name__ == "__main__":
    page_render()

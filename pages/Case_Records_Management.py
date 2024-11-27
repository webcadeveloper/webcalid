import streamlit as st
from database import get_db_connection
from utils.auth_utils import check_authentication, check_role
from utils.i18n import I18nManager
from utils.phone_call import PhoneCallPage

def page_render():
    # Check authentication and role
    check_authentication()
    
    i18n = I18nManager()
    _ = i18n.get_text

    st.title("Gestión de Casos")

    # Apply matrix theme
    st.markdown("""
    <style>
    .case-card {
        background-color: rgba(10, 58, 10, 0.1);
        border: 1px solid #0a3a0a;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
    }
    .case-card:hover {
        background-color: rgba(10, 58, 10, 0.2);
        border-color: #0f0;
    }
    .required-field::after {
        content: " *";
        color: #f00;
    }
    .phone-button {
        background-color: rgba(10, 58, 10, 0.1);
        color: #0f0;
        border: 1px solid #0f0;
        padding: 0.5rem 1rem;
        border-radius: 4px;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    .phone-button:hover {
        background-color: rgba(10, 58, 10, 0.2);
    }
    </style>
    """, unsafe_allow_html=True)

    # Get current user's cases
    conn = get_db_connection()
    cur = conn.cursor()

    # Create new case form
    st.subheader("Registrar Nuevo Caso")
    with st.form("new_case_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            first_name = st.text_input("Nombre", key="first_name")
            st.markdown('<p class="required-field">Campo requerido</p>', unsafe_allow_html=True)
            
            last_name = st.text_input("Apellido", key="last_name")
            st.markdown('<p class="required-field">Campo requerido</p>', unsafe_allow_html=True)
            
            a_number = st.text_input("Número A (9 dígitos)", key="a_number")
            st.markdown('<p class="required-field">Campo requerido</p>', unsafe_allow_html=True)
            
            court_address = st.text_area("Dirección de la Corte", key="court_address")
            st.markdown('<p class="required-field">Campo requerido</p>', unsafe_allow_html=True)
            
        with col2:
            court_phone = st.text_input("Teléfono de la Corte", key="court_phone")
            st.markdown('<p class="required-field">Campo requerido</p>', unsafe_allow_html=True)
            
            client_phone = st.text_input("Teléfono del Cliente", key="client_phone")
            
            other_client_phone = st.text_input("Teléfono Alternativo", key="other_client_phone")
            
            client_address = st.text_area("Dirección del Cliente", key="client_address")
            client_email = st.text_input("Email del Cliente", key="client_email")

        submitted = st.form_submit_button("Guardar Caso")
        
        if submitted:
            # Validate required fields
            required_fields = {
                'Nombre': first_name,
                'Apellido': last_name,
                'Número A': a_number,
                'Dirección de la Corte': court_address,
                'Teléfono de la Corte': court_phone
            }
            
            missing_fields = [field for field, value in required_fields.items() if not value]
            
            if missing_fields:
                st.error(f"Por favor complete los siguientes campos requeridos: {', '.join(missing_fields)}")
            elif not a_number.isdigit() or len(a_number) != 9:
                st.error("El Número A debe contener exactamente 9 dígitos")
            else:
                try:
                    # Insert new case
                    cur.execute("""
                        INSERT INTO cases (
                            first_name, last_name, a_number, court_address, court_phone,
                            client_phone, other_client_phone, client_address, client_email,
                            created_by
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING id
                    """, (
                        first_name, last_name, a_number, court_address, court_phone,
                        client_phone, other_client_phone, client_address, client_email,
                        st.session_state.user_id
                    ))
                    case_id = cur.fetchone()[0]
                    conn.commit()
                    st.success("Caso registrado exitosamente")
                    
                    # Initialize phone call for the new case if client phone is provided
                    if client_phone:
                        st.session_state.current_case = case_id
                        st.session_state.current_phone = client_phone
                        st.rerun()
                        
                except Exception as e:
                    conn.rollback()
                    st.error(f"Error al guardar el caso: {str(e)}")

    # Display user's cases
    st.subheader("Mis Casos")
    cur.execute("""
        SELECT id, first_name, last_name, a_number, court_address, court_phone,
               client_phone, other_client_phone, client_address, client_email
        FROM cases 
        WHERE created_by = %s 
        ORDER BY created_at DESC
    """, (st.session_state.user_id,))
    cases = cur.fetchall()

    if not cases:
        st.info("No hay casos registrados")
    else:
        for case in cases:
            with st.container():
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.markdown(f"""
                    <div class="case-card">
                        <h3>{case[1]} {case[2]}</h3>
                        <p><strong>Número A:</strong> {case[3]}</p>
                        <p><strong>Dirección de la Corte:</strong> {case[4]}</p>
                        <p><strong>Teléfono de la Corte:</strong> {case[5]}</p>
                        <p><strong>Teléfono del Cliente:</strong> {case[6] or 'No registrado'}</p>
                        <p><strong>Teléfono Alternativo:</strong> {case[7] or 'No registrado'}</p>
                        <p><strong>Dirección del Cliente:</strong> {case[8] or 'No registrada'}</p>
                        <p><strong>Email del Cliente:</strong> {case[9] or 'No registrado'}</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    if case[6]:  # If client_phone exists
                        if st.button(f"📞 Llamar", key=f"call_{case[0]}", help="Iniciar llamada con el cliente"):
                            st.session_state.current_case = case[0]
                            st.session_state.current_phone = case[6]
                            st.rerun()
                            
                    if case[7]:  # If other_client_phone exists
                        if st.button(f"📞 Llamar Alt.", key=f"call_alt_{case[0]}", help="Iniciar llamada al teléfono alternativo"):
                            st.session_state.current_case = case[0]
                            st.session_state.current_phone = case[7]
                            st.rerun()

    # Handle active call
    if 'current_case' in st.session_state and 'current_phone' in st.session_state:
        st.subheader("Llamada Activa")
        phone_page = PhoneCallPage()
        phone_page.render()

    # Cleanup
    cur.close()
    conn.close()

if __name__ == "__main__":
    page_render()

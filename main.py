import streamlit as st
import database
from utils import hash_password, verify_password
from database import get_db_connection

# Initialize the database
database.init_db()

def main():
    st.set_page_config(
        page_title="Information Dashboard",
        page_icon="🔍",
        layout="wide"
    )

    # Initialize session state
    if 'user_id' not in st.session_state:
        st.session_state.user_id = None
    if 'is_supervisor' not in st.session_state:
        st.session_state.is_supervisor = False

    # Login/Register interface if not logged in
    if not st.session_state.user_id:
        st.title("Welcome to Information Dashboard")
        
        tab1, tab2 = st.tabs(["Login", "Register"])
        
        with tab1:
            st.subheader("Login")
            username = st.text_input("Username", key="login_username")
            password = st.text_input("Password", type="password", key="login_password")
            
            if st.button("Login"):
                conn = database.get_db_connection()
                cur = conn.cursor()
                cur.execute(
                    "SELECT id, password_hash, is_supervisor FROM users WHERE username = %s",
                    (username,)
                )
                user = cur.fetchone()
                cur.close()
                conn.close()

                if user and verify_password(user[1], password):
                    st.session_state.user_id = user[0]
                    st.session_state.is_supervisor = user[2]
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error("Invalid username or password")

        with tab2:
            st.subheader("Register")
            new_username = st.text_input("Username", key="register_username")
            new_password = st.text_input("Password", type="password", key="register_password")
            confirm_password = st.text_input("Confirm Password", type="password")
            is_supervisor = st.checkbox("Register as Supervisor")

            if st.button("Register"):
                if new_password != confirm_password:
                    st.error("Passwords do not match")
                    return

                try:
                    conn = database.get_db_connection()
                    cur = conn.cursor()
                    cur.execute(
                        "INSERT INTO users (username, password_hash, is_supervisor) VALUES (%s, %s, %s)",
                        (new_username, hash_password(new_password), is_supervisor)
                    )
                    conn.commit()
                    cur.close()
                    conn.close()
                    st.success("Registration successful! Please login.")
                except Exception as e:
                    st.error("Username already exists or registration failed")

    else:
        # Sidebar Navigation
        st.sidebar.title("Navigation")
        
        # Add navigation links
        pages = {
            "Home": "/",
            "Number Search": "/Number_Search",
            "Supervisor Dashboard": "/Supervisor_Dashboard" if st.session_state.is_supervisor else None
        }
        
        # Only show valid pages for the user's role
        for page_name, page_url in pages.items():
            if page_url is not None:
                if st.sidebar.button(page_name):
                    st.experimental_set_query_params(page=page_url.strip('/'))
                    st.rerun()
        
        # Show logout button in sidebar
        if st.sidebar.button("Logout"):
            st.session_state.clear()
            st.rerun()

        # Main dashboard welcome message and profile settings
        st.title("Panel de Control")
        
        # User profile section
        st.header("Perfil de Usuario")
        
        # Get current PDL API key
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT pdl_api_key FROM users WHERE id = %s", (st.session_state.user_id,))
        user_data = cur.fetchone()
        current_pdl_key = user_data[0] if user_data else ""
        cur.close()
        conn.close()
        
        # PDL API Key input
        pdl_api_key = st.text_input(
            "Clave API de People Data Labs",
            value=current_pdl_key,
            type="password",
            help="Ingrese su clave API de People Data Labs"
        )
        
        if st.button("Actualizar Clave API"):
            if pdl_api_key and len(pdl_api_key) > 20:
                conn = get_db_connection()
                cur = conn.cursor()
                cur.execute(
                    "UPDATE users SET pdl_api_key = %s WHERE id = %s",
                    (pdl_api_key, st.session_state.user_id)
                )
                conn.commit()
                cur.close()
                conn.close()
                st.success("¡Clave API actualizada exitosamente!")
            else:
                st.error("La clave API no es válida. Debe tener al menos 20 caracteres.")
        
        st.write("Use el menú lateral para navegar por las diferentes secciones.")

if __name__ == "__main__":
    main()

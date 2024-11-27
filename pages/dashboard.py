import streamlit as st
from database import get_cases_by_user

class DashboardApp:
    def run(self):
        st.title("Dashboard de Operador")

        # Obtener casos del usuario actual
        user_id = st.session_state.get('user_id')
        cases = get_cases_by_user(user_id)

        # Mostrar lista de casos
        st.subheader("Casos Asignados")
        if cases:
            for case in cases:
                with st.expander(f"Caso #{case['number']}"):
                    st.write(f"Estado: {case['status']}")
                    st.write(f"Nombre: {case['first_name']} {case['last_name']}")
                    st.write(f"Número A: {case['a_number']}")
                    st.write(f"Dirección de la Corte: {case['court_address']}")
                    st.write(f"Teléfono de la Corte: {case['court_phone']}")
                    st.write(f"Teléfono del Cliente: {case['client_phone']}")
                    st.write(f"Otro Teléfono del Cliente: {case['other_client_phone']}")
                    st.write(f"Dirección del Cliente: {case['client_address']}")
                    st.write(f"Email del Cliente: {case['client_email']}")
        else:
            st.write("No hay casos asignados a este usuario.")
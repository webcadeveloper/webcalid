import streamlit as st
import random

class NumberGenerator:
    def __init__(self):
        self.used_numbers = set()
        self.initialize_session_state()

    def initialize_session_state(self):
        """Initialize session state variables"""
        if 'generated_numbers' not in st.session_state:
            st.session_state.generated_numbers = []
        if 'current_prefix' not in st.session_state:
            st.session_state.current_prefix = 244206

    def generate_number(self):
        """Generate a new unique number"""
        while True:
            new_number = str(st.session_state.current_prefix * 1000 + 
                           len(st.session_state.generated_numbers)).zfill(9)
            if new_number not in self.used_numbers:
                self.used_numbers.add(new_number)
                return new_number

    def generate_random_number(self):
        """Generate a random number"""
        while True:
            new_number = str(random.randint(100000000, 999999999))
            if new_number not in self.used_numbers:
                self.used_numbers.add(new_number)
                return new_number

    def reset(self):
        """Reset the generator state"""
        self.used_numbers.clear()
        st.session_state.generated_numbers = []
        st.session_state.current_prefix = 244206

    def run(self):
        """Main interface for number generation"""
        if not st.session_state.get('user_id'):
            st.warning("Por favor inicie sesión")
            st.stop()
            return

        st.title("Generador de Números")

        # Display current number
        current_number = (st.session_state.generated_numbers[-1] 
                        if st.session_state.generated_numbers 
                        else "000000000")
        st.markdown(f'<div class="number-display">{current_number}</div>', 
                   unsafe_allow_html=True)

        # Control buttons
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("Generar Siguiente Número", type="primary"):
                new_number = self.generate_number()
                st.session_state.generated_numbers.append(new_number)
                st.success(f"Nuevo número generado: {new_number}")
                st.rerun()

        with col2:
            if st.button("Generar Número Aleatorio", type="secondary"):
                new_number = self.generate_random_number()
                st.session_state.generated_numbers.append(new_number)
                st.success(f"Número aleatorio generado: {new_number}")
                st.rerun()

        with col3:
            if st.button("Reiniciar", type="secondary"):
                self.reset()
                st.success("Generador reiniciado")
                st.rerun()

        # History section
        if st.session_state.generated_numbers:
            st.subheader("Historial de Números")
            history_df = pd.DataFrame({
                'Número': st.session_state.generated_numbers[::-1]
            })
            st.dataframe(history_df, use_container_width=True)

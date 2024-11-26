import streamlit as st
from utils.pdl_scraper import PDLScraper
import pyperclip
import time

def page_render():
    if not st.session_state.get('user_id'):
        st.warning("Por favor inicie sesión")
        st.stop()
        return

    # Initialize session state
    if 'generated_numbers' not in st.session_state:
        st.session_state.generated_numbers = []
    if 'current_prefix' not in st.session_state:
        st.session_state.current_prefix = 244206

    # Apply matrix style
    st.markdown("""
    <style>
        .main {
            background-color: black;
        }
        .number-display {
            font-family: 'Courier New', Courier, monospace;
            font-size: 2.5rem;
            font-weight: bold;
            color: #0f0;
            text-shadow: 0 0 15px #0f0;
            animation: glow 1.5s ease-in-out infinite alternate;
            padding: 1rem;
            margin: 1rem 0;
            background: rgba(0, 255, 0, 0.1);
            border: 2px solid #0f0;
            border-radius: 10px;
        }
        .number-list {
            list-style-type: none;
            padding: 0;
            margin: 1rem 0;
        }
        .number-item {
            font-family: 'Courier New', Courier, monospace;
            color: #0f0;
            text-shadow: 0 0 10px #0f0;
            padding: 0.5rem;
            margin: 0.5rem 0;
            background: rgba(0, 255, 0, 0.05);
            border: 1px solid #0f0;
            border-radius: 5px;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        .number-item:hover {
            background: rgba(0, 255, 0, 0.1);
            text-shadow: 0 0 20px #0f0;
        }
        @keyframes glow {
            from {
                text-shadow: 0 0 5px #0f0, 0 0 10px #0f0, 0 0 15px #0f0;
            }
            to {
                text-shadow: 0 0 10px #0f0, 0 0 20px #0f0, 0 0 30px #0f0;
            }
        }
        .stButton>button {
            background-color: rgba(0, 255, 0, 0.1);
            color: #0f0;
            border: 2px solid #0f0;
            transition: all 0.3s ease;
        }
        .stButton>button:hover {
            background-color: rgba(0, 255, 0, 0.2);
            border-color: #0f0;
        }
    </style>
    """, unsafe_allow_html=True)

    st.title("Generador de Números")

    # Display current number with matrix effect
    if st.session_state.generated_numbers:
        current_number = st.session_state.generated_numbers[-1]
    else:
        current_number = "000000000"
    
    st.markdown(f'<div class="number-display">{current_number}</div>', unsafe_allow_html=True)

    # Control buttons
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Generar Siguiente Número"):
            new_number = str(st.session_state.current_prefix * 1000 + len(st.session_state.generated_numbers)).zfill(9)
            st.session_state.generated_numbers.append(new_number)
            st.session_state.current_prefix += 1

            # PDL API Integration
            pdl_scraper = PDLScraper()
            if st.session_state.get('pdl_api_key'):
                pdl_scraper.api_key = st.session_state.pdl_api_key
                result = pdl_scraper.search(new_number)
                if result['status'] == 'success':
                    st.success("¡Número encontrado en PDL!")
                    st.json(result['data'])

    with col2:
        if st.button("Copiar Último Número") and st.session_state.generated_numbers:
            pyperclip.copy(st.session_state.generated_numbers[-1])
            st.success("¡Número copiado al portapapeles!")

    # Display number history
    if st.session_state.generated_numbers:
        st.markdown("<h3>Historial de Números</h3>", unsafe_allow_html=True)
        for number in reversed(st.session_state.generated_numbers):
            st.markdown(f'<div class="number-item" onclick="navigator.clipboard.writeText(\'{number}\')">{number}</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    page_render()

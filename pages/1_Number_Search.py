import streamlit as st
import pandas as pd
from utils import generate_sequential_number, generate_random_number, export_to_excel
from database import add_search_history, get_db_connection, add_phone_call

def number_search_page():
    try:
        st.title("Búsqueda por Número")
        
        # Initialize session state
        if 'continuous_search_active' not in st.session_state:
            st.session_state.continuous_search_active = False
        if 'search_stats' not in st.session_state:
            st.session_state.search_stats = None
        if 'last_search_error' not in st.session_state:
            st.session_state.last_search_error = None
        if 'search_attempts' not in st.session_state:
            st.session_state.search_attempts = 0
        
        # Number generation section
        st.header("Generar Número")
        
        col1, col2 = st.columns(2)
        
        with col1:
            generation_method = st.radio(
                "Método de Generación",
                ["Secuencial", "Aleatorio", "Búsqueda Continua"]
            )
        
        with col2:
            if generation_method == "Secuencial":
                start_number = st.number_input("Comenzar Desde", min_value=0, max_value=999999999, value=0)
                generated_number = generate_sequential_number(start_number)
            elif generation_method == "Búsqueda Continua":
                start_number = st.number_input("Número Inicial", min_value=0, max_value=999999999, value=100000000)
                max_attempts = st.number_input("Intentos Máximos", min_value=1, value=1000)
                delay = st.slider("Pausa entre intentos (segundos)", 0.1, 5.0, 1.0)
                
                if not st.session_state.continuous_search_active:
                    if st.button("Iniciar Búsqueda"):
                        st.session_state.continuous_search_active = True
                        st.session_state.search_attempts = 0
                else:
                    if st.button("Detener Búsqueda"):
                        st.session_state.continuous_search_active = False
                
                generated_number = str(start_number)
            else:
                generated_number = generate_random_number()
                if st.button("Generar Nuevo Número"):
                    generated_number = generate_random_number()
        
        # Display generated number with matrix effect
        st.markdown("""
        <style>
        .matrix-number {
            font-family: 'Courier New', monospace;
            font-size: 2.5rem;
            font-weight: bold;
            color: #0f0;
            text-shadow: 0 0 10px #0f0;
            padding: 1rem;
            border: 2px solid #0f0;
            border-radius: 5px;
            margin: 1rem 0;
            background: rgba(0, 0, 0, 0.2);
            animation: glow 1.5s ease-in-out infinite alternate;
        }

        @keyframes glow {
            from {
                text-shadow: 0 0 5px #0f0, 0 0 10px #0f0, 0 0 15px #0f0;
            }
            to {
                text-shadow: 0 0 10px #0f0, 0 0 20px #0f0, 0 0 30px #0f0;
            }
        }
        </style>
        """, unsafe_allow_html=True)

        st.markdown(f'<div class="matrix-number">{generated_number}</div>', unsafe_allow_html=True)

        # Search section with tabs
        st.header("Resultados de Búsqueda")
        
        tabs = st.tabs(["EOIR", "Registros Públicos", "Redes Sociales"])
        
        # URLs for different searches
        search_urls = {
            "EOIR": f"https://acis.eoir.justice.gov/es/",
            "public": f"https://www.whitepages.com/search/person?q={generated_number}",
            "social": f"https://www.uscis.gov/es/registros-publicos?number={generated_number}"
        }
        
        # Function to create search frame with error handling
        def create_search_frame(url, source_name):
            with st.spinner(f"Cargando datos de {source_name}..."):
                try:
                    st.markdown(f'<iframe src="{url}" height="500" width="100%" style="border: 1px solid #ddd; border-radius: 5px;"></iframe>', unsafe_allow_html=True)
                    
                    # Add verification button
                    if st.button(f"✓ Confirmar {source_name}"):
                        st.success(f"¡Datos de {source_name} confirmados!")
                        st.session_state[f"{source_name.lower()}_verified"] = True
                        return True
                except Exception as e:
                    st.error(f"Error al cargar {source_name}: {str(e)}")
                    if st.button("Reintentar"):
                        st.rerun()
                    return False
            return False
        
        # Handle each search tab
        for tab, (source, url) in zip(tabs, search_urls.items()):
            with tab:
                success = create_search_frame(url, source)
        
        # Save results
        if st.button("Guardar Búsqueda"):
            try:
                results = {
                    source: st.session_state.get(f"{source.lower()}_verified", False)
                    for source in search_urls.keys()
                }
                add_search_history(
                    st.session_state.user_id,
                    generated_number,
                    any(results.values()),
                    results
                )
                st.success("¡Búsqueda guardada exitosamente!")
            except Exception as e:
                st.error(f"Error al guardar la búsqueda: {str(e)}")

    except Exception as e:
        st.error(f"Error en la aplicación: {str(e)}")
        if st.button("Reiniciar"):
            st.rerun()

if __name__ == "__main__":
    number_search_page()
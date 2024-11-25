import streamlit as st
import pandas as pd
from utils import generate_sequential_number, generate_random_number, export_to_excel
from database import add_search_history, get_db_connection, add_phone_call

def number_search_page():
    try:
        st.title("Búsqueda por Número")
        
        # CSS for matrix effect and loading indicators
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
                cursor: pointer;
                transition: all 0.3s;
                text-align: center;
                margin: 1rem 0;
                background: rgba(0, 0, 0, 0.2);
            }
            .matrix-number:hover {
                background: rgba(0, 255, 0, 0.1);
                transform: scale(1.02);
            }
            .search-frame {
                width: 100%;
                height: 500px;
                border: 2px solid #0f0;
                border-radius: 5px;
                background: white;
            }
            .loading-indicator {
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100px;
            }
            .progress-bar {
                width: 100%;
                height: 4px;
                background: #ddd;
                border-radius: 2px;
                overflow: hidden;
            }
            .progress-value {
                width: 0%;
                height: 100%;
                background: #0f0;
                animation: progress 1s ease infinite;
            }
            @keyframes progress {
                0% { width: 0%; }
                100% { width: 100%; }
            }
            </style>
        """, unsafe_allow_html=True)
        
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
                start_number = st.number_input("Comenzar Desde", min_value=0, value=0)
                generated_number = generate_sequential_number(start_number)
            elif generation_method == "Búsqueda Continua":
                start_number = st.number_input("Número Inicial", min_value=0, value=10000000)
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
        
        # Display generated number with click-to-copy functionality
        st.subheader("Número Generado:")
        st.markdown(f"""
            <div class="matrix-number" id="generated-number" onclick="copyNumber('{generated_number}')">
                {generated_number}
            </div>
            <script>
            function copyNumber(number) {{
                navigator.clipboard.writeText(number)
                    .then(() => {{
                        const element = document.getElementById('generated-number');
                        element.style.color = '#0ff';
                        element.style.borderColor = '#0ff';
                        setTimeout(() => {{
                            element.style.color = '#0f0';
                            element.style.borderColor = '#0f0';
                        }}, 500);
                    }})
                    .catch(err => console.error('Error copying:', err));
            }}
            </script>
        """, unsafe_allow_html=True)
        
        # Search section
        st.header("Resultados de Búsqueda")
        
        # Create tabs for different data sources
        tabs = st.tabs(["EOIR", "Registros Públicos", "Redes Sociales", "Registros de Negocios"])
        
        # URLs for different searches
        search_urls = {
            "EOIR": "https://acis.eoir.justice.gov/es/",
            "public": f"https://www.whitepages.com/search/person?q={generated_number}",
            "social": f"https://www.uscis.gov/es/registros-publicos?number={generated_number}",
            "business": f"https://www.dnb.com/business-directory/company-search.html?term={generated_number}"
        }
        
        # Function to create search frame with error handling
        def create_search_frame(url, source_name):
            try:
                with st.spinner(f"Cargando datos de {source_name}..."):
                    st.markdown(f"""
                        <iframe 
                            src="{url}" 
                            class="search-frame"
                            sandbox="allow-same-origin allow-scripts allow-forms"
                            loading="lazy"
                        ></iframe>
                    """, unsafe_allow_html=True)
                    
                    # Add verification button
                    if st.button(f"✓ Confirmar {source_name}"):
                        st.success(f"¡Datos de {source_name} confirmados!")
                        return True
            except Exception as e:
                st.error(f"Error al cargar {source_name}: {str(e)}")
                if st.button("Reintentar"):
                    st.experimental_rerun()
                return False
            return False
        
        # Handle each search tab
        for idx, (tab, (source, url)) in enumerate(zip(tabs, search_urls.items())):
            with tab:
                success = create_search_frame(url, source)
                if success:
                    st.session_state[f"{source.lower()}_verified"] = True
        
        # Save results
        st.header("Guardar Resultados")
        if st.button("Guardar Búsqueda"):
            results = {
                source: st.session_state.get(f"{source.lower()}_verified", False)
                for source in search_urls.keys()
            }
            try:
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
        if st.button("Reiniciar Aplicación"):
            st.experimental_rerun()

if __name__ == "__main__":
    number_search_page()
import streamlit as st
import random
from utils import check_authentication
from scrapers.pdl_scraper import PDLScraper
from database import get_db_connection

def generate_random_suffix():
    return random.randint(100000, 999999)

def generate_next_number(current_prefix):
    random_suffix = generate_random_suffix()
    new_number = current_prefix * 1000 + random_suffix
    return str(new_number).zfill(9)

def generate_random_number():
    prefix = random.randint(100, 999)
    suffix = random.randint(100000, 999999)
    return str(prefix * 1000 + suffix).zfill(9)

import threading
from scrapers.eoir_scraper import EOIRScraper

def number_search_page():
    check_authentication()
    
    st.title("Búsqueda por Número")
    
    # Initialize session state for search control
    if 'search_running' not in st.session_state:
        st.session_state.search_running = False
    if 'stop_search' not in st.session_state:
        st.session_state.stop_search = threading.Event()
    if 'search_stats' not in st.session_state:
        st.session_state.search_stats = {
            'total_attempts': 0,
            'successful_attempts': 0,
            'not_found_attempts': 0,
            'failed_attempts': 0,
            'cache_errors': 0,
            'last_number': None,
            'last_error': None
        }
    
    # Initialize session state
    if 'current_prefix' not in st.session_state:
        st.session_state.current_prefix = 244206
    if 'generated_numbers' not in st.session_state:
        st.session_state.generated_numbers = []
    
    # Number generation section
    st.header("Generar Número")
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        if st.button("Generar Siguiente Número"):
            new_number = generate_next_number(st.session_state.current_prefix)
            st.session_state.generated_numbers.append(new_number)
            st.session_state.current_prefix += 1
        
        if st.button("Generar Número Aleatorio"):
            random_number = generate_random_number()
            st.session_state.generated_numbers.append(random_number)
    
    with col2:
        # Display current or generate new number
        if st.session_state.generated_numbers:
            current_number = st.session_state.generated_numbers[-1]
        else:
            current_number = generate_next_number(st.session_state.current_prefix)
            st.session_state.generated_numbers.append(current_number)
            st.session_state.current_prefix += 1
        
        # Display generated number with matrix effect
        st.markdown("""
        <style>
        .matrix-number {
            font-family: 'Courier New', monospace;
            font-size: 3rem;
            font-weight: bold;
            letter-spacing: 0.25em;
            color: #00ff00;
            text-shadow: 0 0 5px rgba(0, 255, 0, 0.5);
            padding: 1.5rem;
            border: 2px solid rgba(0, 255, 0, 0.5);
            border-radius: 8px;
            background: rgba(0, 0, 0, 0.85);
            animation: glow 2s ease-in-out infinite alternate;
            display: inline-block;
        }
        @keyframes glow {
            from {
                text-shadow: 0 0 2px rgba(0, 255, 0, 0.4),
                            0 0 4px rgba(0, 255, 0, 0.3);
                border-color: rgba(0, 255, 0, 0.4);
            }
            to {
                text-shadow: 0 0 4px rgba(0, 255, 0, 0.5),
                            0 0 8px rgba(0, 255, 0, 0.4);
                border-color: rgba(0, 255, 0, 0.6);
            }
        }
        </style>
        """, unsafe_allow_html=True)
        
        st.markdown(f'<div class="matrix-number">{current_number}</div>', unsafe_allow_html=True)
    
    # Display generated numbers list in a horizontal grid
    if st.session_state.generated_numbers:
        st.header("Números Generados")
        
        # Add JavaScript for copy functionality
        st.markdown("""
        <script>
        function copyNumber(number) {
            navigator.clipboard.writeText(number).then(function() {
                // Show success message
                const tooltip = document.getElementById('tooltip-' + number);
                tooltip.style.opacity = '1';
                setTimeout(() => { tooltip.style.opacity = '0'; }, 1500);
            });
        }
        </script>
        """, unsafe_allow_html=True)
        
        # Add CSS for the grid layout and copy button
        st.markdown("""
        <style>
        .number-grid {
            display: flex;
            flex-wrap: wrap;
            gap: 1rem;
            justify-content: flex-start;
        }
        .number-container {
            position: relative;
            display: flex;
            flex-direction: column;
            align-items: center;
        }
        .matrix-number-small {
            font-family: 'Courier New', monospace;
            font-size: 1.2rem;
            color: #00ff00;
            text-shadow: 0 0 3px #00ff00;
            padding: 0.5rem 1rem;
            border: 2px solid rgba(0, 255, 0, 0.5);
            border-radius: 4px;
            background: rgba(0, 0, 0, 0.85);
            margin-bottom: 0.5rem;
            animation: glow 2s ease-in-out infinite alternate;
        }
        .copy-button {
            font-family: 'Courier New', monospace;
            padding: 0.3rem 0.8rem;
            background: rgba(0, 255, 0, 0.2);
            border: 1px solid #00ff00;
            color: #00ff00;
            border-radius: 3px;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        .copy-button:hover {
            background: rgba(0, 255, 0, 0.3);
            text-shadow: 0 0 5px #00ff00;
        }
        .tooltip {
            position: absolute;
            bottom: -25px;
            background: rgba(0, 255, 0, 0.9);
            color: black;
            padding: 0.3rem;
            border-radius: 3px;
            font-size: 0.8rem;
            opacity: 0;
    # Búsqueda Continua
    st.header("Búsqueda Continua")
    
    search_col1, search_col2 = st.columns([2, 1])
    
    with search_col1:
        if not st.session_state.search_running:
            if st.button("Iniciar Búsqueda Continua", type="primary"):
                st.session_state.search_running = True
                st.session_state.stop_search.clear()
                st.experimental_rerun()
        else:
            if st.button("Detener Búsqueda", type="secondary"):
                st.session_state.stop_search.set()
                st.session_state.search_running = False
                st.experimental_rerun()
    
    with search_col2:
        st.metric("Total Intentos", st.session_state.search_stats['total_attempts'])
    
    # Mostrar estadísticas en tiempo real
    if st.session_state.search_running:
        progress_placeholder = st.empty()
        stats_col1, stats_col2, stats_col3 = st.columns(3)
        
        with stats_col1:
            st.metric("Búsquedas Exitosas", 
                     st.session_state.search_stats['successful_attempts'])
        with stats_col2:
            st.metric("No Encontrados", 
                     st.session_state.search_stats['not_found_attempts'])
        with stats_col3:
            st.metric("Errores", 
                     st.session_state.search_stats['failed_attempts'])
        
        # Mostrar último error si existe
        if st.session_state.search_stats['last_error']:
            st.warning(f"Último error: {st.session_state.search_stats['last_error']}")
        
        # Iniciar búsqueda en un thread separado
        scraper = EOIRScraper()
        current_number = st.session_state.current_prefix * 1000000
        
        def update_progress(progress, number):
            progress_placeholder.progress(progress / 100)
            st.session_state.search_stats.update(scraper.get_search_stats())
            st.experimental_rerun()
        
        result = scraper.search_until_found(
            str(current_number),
            max_attempts=1000,
            delay=1.0,
            progress_callback=update_progress,
            stop_flag=st.session_state.stop_search
        )
        
        if result['status'] == 'found':
            st.success(f"¡Caso encontrado! Número: {result['found_case']['number']}")
            st.session_state.search_running = False
            transition: opacity 0.3s;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Create grid container
        st.markdown('<div class="number-grid">', unsafe_allow_html=True)
        
        # Display numbers in grid
        for number in reversed(st.session_state.generated_numbers[-10:]):
            st.markdown(f"""
            <div class="number-container">
                <div class="matrix-number-small">{number}</div>
                <button class="copy-button" onclick="copyNumber('{number}')">Copiar</button>
                <div class="tooltip" id="tooltip-{number}">¡Copiado!</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Add iframes for external searches using HTML components
    st.header("Búsqueda Externa")
    
    tabs = st.tabs(["EOIR", "Registros Públicos", "Redes Sociales"])
    
    with tabs[0]:
        st.markdown(f'<iframe src="https://acis.eoir.justice.gov/en/" width="100%" height="600" frameborder="0"></iframe>', unsafe_allow_html=True)
    
    with tabs[1]:
        st.markdown(f'<iframe src="https://www.whitepages.com/search/person?q={current_number}" width="100%" height="600" frameborder="0"></iframe>', unsafe_allow_html=True)
    
    with tabs[2]:
        st.markdown(f'<iframe src="https://www.uscis.gov/es/registros-publicos?number={current_number}" width="100%" height="600" frameborder="0"></iframe>', unsafe_allow_html=True)

if __name__ == "__main__":
    number_search_page()

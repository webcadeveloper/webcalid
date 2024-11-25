import streamlit as st
from utils.auth_utils import check_authentication
from scrapers.eoir_scraper import EOIRScraper
import threading

def number_search_page():
    check_authentication()
    st.title("Búsqueda por Número")

    # Inicializar estado de sesión
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
            'last_number': None,
            'last_error': None
        }

    # Generar números
    st.header("Generar Número")
    col1, col2 = st.columns([1, 3])

    with col1:
        if st.button("Generar Siguiente Número"):
            st.session_state.generated_numbers.append(generate_next_number())
        if st.button("Generar Número Aleatorio"):
            st.session_state.generated_numbers.append(generate_random_number())

    with col2:
        current_number = st.session_state.generated_numbers[-1] if st.session_state.generated_numbers else generate_next_number()
        st.markdown(f'<div class="matrix-number">{current_number}</div>', unsafe_allow_html=True)

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

    if st.session_state.search_running:
        progress_placeholder = st.empty()
        stats_col1, stats_col2, stats_col3 = st.columns(3)

        with stats_col1:
            st.metric("Búsquedas Exitosas", st.session_state.search_stats['successful_attempts'])
        with stats_col2:
            st.metric("No Encontrados", st.session_state.search_stats['not_found_attempts'])
        with stats_col3:
            st.metric("Errores", st.session_state.search_stats['failed_attempts'])

        if st.session_state.search_stats['last_error']:
            st.warning(f"Último error: {st.session_state.search_stats['last_error']}")

        scraper = EOIRScraper()
        current_number = st.session_state.current_prefix * 1000000
        result = scraper.search_until_found(
            str(current_number),
            max_attempts=1000,
            delay=1.0,
            progress_callback=lambda p, n: update_progress(p, n),
            stop_flag=st.session_state.stop_search
        )

        if result['status'] == 'found':
            st.success(f"¡Caso encontrado! Número: {result['found_case']['number']}")
            st.session_state.search_running = False

def generate_next_number():
    return str(st.session_state.current_prefix * 1000 + random.randint(100000, 999999)).zfill(9)

def generate_random_number():
    return str(random.randint(100000, 999999999)).zfill(9)

def update_progress(progress, number):
    progress_placeholder.progress(progress / 100)
    st.session_state.search_stats.update(scraper.get_search_stats())
    st.experimental_rerun()
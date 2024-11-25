import streamlit as st
import pandas as pd
import tempfile
from utils import generate_sequential_number, generate_random_number
from database import add_search_history, get_db_connection, add_phone_call

def number_search_page():
    try:
        st.title("Búsqueda por Número")
        
        # CSS for matrix effect
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
                transition: color 0.3s;
                text-align: center;
                margin: 1rem 0;
            }
            </style>
        """, unsafe_allow_html=True)
        
        # Initialize session state
        if 'call_active' not in st.session_state:
            st.session_state.call_active = False
        if 'current_call_id' not in st.session_state:
            st.session_state.current_call_id = None
        if 'continuous_search_active' not in st.session_state:
            st.session_state.continuous_search_active = False
        if 'search_stats' not in st.session_state:
            st.session_state.search_stats = None
        
        # Number generation section
        st.header("Generate Number")
        
        col1, col2 = st.columns(2)
        
        with col1:
            generation_method = st.radio(
                "Método de Búsqueda",
                ["Secuencial", "Aleatorio", "Búsqueda Continua"]
            )
        
        with col2:
            if generation_method == "Secuencial":
                start_number = st.number_input("Start From", min_value=0, value=0)
                generated_number = generate_sequential_number(start_number)
            elif generation_method == "Búsqueda Continua":
                start_number = st.number_input("Número Inicial", min_value=0, value=10000000)
                max_attempts = st.number_input("Intentos Máximos", min_value=1, value=1000)
                delay = st.slider("Pausa entre intentos (segundos)", 0.1, 5.0, 1.0)
                
                col1, col2 = st.columns(2)
                with col1:
                    if not st.session_state.continuous_search_active:
                        if st.button("Iniciar Búsqueda Continua"):
                            st.session_state.continuous_search_active = True
                            st.session_state.eoir_scraper.reset_stats()
                    else:
                        if st.button("Detener Búsqueda"):
                            st.session_state.continuous_search_active = False
                
                if st.session_state.continuous_search_active:
                    result = st.session_state.eoir_scraper.search_until_found(
                        str(start_number),
                        max_attempts=max_attempts,
                        delay=delay
                    )
                    
                    # Update stats
                    st.session_state.search_stats = result['stats']
                    
                    # Show progress
                    progress = result['attempts'] / max_attempts
                    st.progress(progress)
                    
                    # Display stats
                    stats = st.session_state.search_stats
                    st.metric("Total de Intentos", stats['total_attempts'])
                    st.metric("Casos Encontrados", stats['successful_attempts'])
                    if stats['last_number']:
                        st.metric("Último Número Probado", stats['last_number'])
                    
                    if result['status'] == 'found':
                        st.success(f"¡Caso encontrado! Número: {result['found_case']['data']['numero_caso']}")
                        generated_number = result['found_case']['data']['numero_caso']
                    elif result['status'] == 'max_attempts_reached':
                        st.warning("Se alcanzó el límite máximo de intentos sin encontrar casos.")
                        st.session_state.continuous_search_active = False
                generated_number = str(start_number)
            else:
                generated_number = generate_random_number()
                if st.button("Generate New Random Number"):
                    generated_number = generate_random_number()
        
        st.subheader("Generated Number:")
        st.markdown(f"""
            <div class="matrix-number" id="generated-number" data-number="{generated_number}"
                 title="Click to copy and search">
                {generated_number}
            </div>
            <div id="search-progress" style="display:none;">
                <div class="progress-bar">
                    <div class="progress-value"></div>
                </div>
                <p class="progress-text">Searching EOIR database...</p>
            </div>
            <script>
                const number = document.querySelector('#generated-number');
                const progress = document.querySelector('#search-progress');
                const progressBar = document.querySelector('.progress-value');
                const progressText = document.querySelector('.progress-text');

                number.addEventListener('click', async () => {{
                    const numberValue = number.dataset.number;
                    // Copy to clipboard
                    await navigator.clipboard.writeText(numberValue);
                    number.style.color = '#0ff';
                    
                    // Show progress
                    progress.style.display = 'block';
                    progressBar.style.width = '0%';
                    progressText.textContent = 'Initiating EOIR search...';
                    
                    // Simulate progress while actual search happens
                    let width = 0;
                    const interval = setInterval(() => {{
                        if (width >= 90) {{
                            clearInterval(interval);
                        }} else {{
                            width += 5;
                            progressBar.style.width = width + '%';
                        }}
                    }}, 100);
                    
                    try {{
                        // Click the EOIR tab to start search
                        const eoirTab = document.querySelector('[data-value="EOIR Records"]');
                        if (eoirTab) {{
                            eoirTab.click();
                        }}
                        
                        progressText.textContent = 'Search complete!';
                        progressBar.style.width = '100%';
                        setTimeout(() => {{
                            progress.style.display = 'none';
                            number.style.color = '#0f0';
                        }}, 1000);
                    }} catch (err) {{
                        progressText.textContent = 'Error during search';
                        console.error('Search error:', err);
                    }}
                }});
            </script>
            <style>
                .progress-bar {{
                    width: 100%;
                    height: 20px;
                    background-color: #1a1a1a;
                    border-radius: 10px;
                    margin: 10px 0;
                }}
                .progress-value {{
                    width: 0%;
                    height: 100%;
                    background-color: #0f0;
                    border-radius: 10px;
                    transition: width 0.3s ease-in-out;
                }}
                .progress-text {{
                    color: #0f0;
                    text-align: center;
                    margin: 5px 0;
                }}
            </style>
        """, unsafe_allow_html=True)
        
        # Add copy button with visual feedback
        if st.button("📋 Copy Number"):
            st.success("Number copied to clipboard!")
        
        # Search section
        st.header("Search Results")
        
        # Create tabs for different data sources
        tab1, tab2, tab3, tab4 = st.tabs(["EOIR Records", "Public Records", "Social Media", "Business Records"])
        
        # Initialize EOIR scraper and cache
        if 'eoir_cache' not in st.session_state:
            from scrapers.eoir_scraper import EOIRScraper, EOIRCache
            st.session_state.eoir_scraper = EOIRScraper()
            st.session_state.eoir_cache = EOIRCache()
        
        # Function to generate URLs based on number
        def get_search_urls(number, name=None):
            base_urls = {
                "public": f"https://www.whitepages.com/phone/{number}",
                "social": f"https://ice.gov/webform/ice-detention-facility-locator-information?number={number}",
                "business": f"https://egov.uscis.gov/casestatus/landing.do?number={number}"
            }
            
            # If we have a name from EOIR results, add it to the public records search
            if name:
                base_urls["public"] = f"https://www.whitepages.com/name/{name}?phone={number}"
            
            return base_urls
        
        # Get EOIR data first to use in other searches
        case_info = None
        if 'eoir_cache' in st.session_state:
            case_info = st.session_state.eoir_cache.get(generated_number)
            if not case_info:
                case_info = st.session_state.eoir_scraper.search(generated_number)
                if case_info['status'] == 'success':
                    st.session_state.eoir_cache.set(generated_number, case_info)
        
        # Extract name from EOIR data if available
        full_name = None
        if case_info and case_info['status'] == 'success' and 'informacion_personal' in case_info['data']:
            personal_info = case_info['data']['informacion_personal']
            if personal_info and 'nombre' in personal_info and 'apellidos' in personal_info:
                full_name = f"{personal_info['nombre']} {personal_info['apellidos']}"
        
        # Generate URLs for the current number
        search_urls = get_search_urls(generated_number, full_name)
        
        # Helper function to create iframe with loading state
        def create_iframe_with_loading(url, source_name):
            with st.spinner(f"Loading {source_name} data..."):
                try:
                    components_container = st.container()
                    with components_container:
                        st.components.v1.iframe(
                            url,
                            height=400,
                            scrolling=True
                        )
                        
                        # Add confirmation button for the source
                        col1, col2 = st.columns([3, 1])
                        with col2:
                            if st.button(f"✓ Confirm {source_name}"):
                                st.success(f"{source_name} data confirmed!")
                except Exception as e:
                    st.error(f"Error loading {source_name}: {str(e)}")
        
        with tab1:
            st.subheader("EOIR Case Information")
            # Try to get cached result first
            cached_result = st.session_state.eoir_cache.get(generated_number)
            
            if cached_result:
                st.success("Retrieved from cache")
                case_info = cached_result
            else:
                with st.spinner("Searching EOIR database..."):
                    case_info = st.session_state.eoir_scraper.search(generated_number)
                    if case_info['status'] == 'success':
                        st.session_state.eoir_cache.set(generated_number, case_info)
            
            if case_info['status'] == 'success':
                st.json(case_info['data'])
                if st.button("✓ Confirm EOIR Data"):
                    st.success("EOIR data confirmed!")
            elif case_info['status'] == 'not_found':
                st.warning("No EOIR case found with this number")
            else:
                st.error(f"Error searching EOIR: {case_info.get('error', 'Unknown error')}")
        
        with tab2:
            create_iframe_with_loading(search_urls["public"], "Public Records")
        
        with tab3:
            create_iframe_with_loading(search_urls["social"], "Social Media")
        
        with tab4:
            create_iframe_with_loading(search_urls["business"], "Business Records")
        
        # WebRTC Call Section
        st.header("Make a Call")
        
        # WebRTC components
        st.markdown("""
            <audio id="remoteAudio" autoplay></audio>
            <script src="/static/webrtc.js"></script>
        """, unsafe_allow_html=True)
        
        # Call controls
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📞 Start Call"):
                st.session_state.call_active = True
                st.session_state.current_call_id = add_phone_call(
                    search_id=st.session_state.get('last_search_id'),
                    phone_number=generated_number,
                    status="initiated"
                )
                st.experimental_rerun()
        
        with col2:
            if st.session_state.get('call_active', False):
                if st.button("🔚 End Call"):
                    if st.session_state.get('current_call_id'):
                        conn = get_db_connection()
                        cur = conn.cursor()
                        cur.execute(
                            "UPDATE phone_calls SET call_status = 'completed' WHERE id = %s",
                            (st.session_state.current_call_id,)
                        )
                        conn.commit()
                        cur.close()
                        conn.close()
                    st.session_state.call_active = False
                    st.experimental_rerun()
        
        with col3:
            if st.session_state.get('call_active', False):
                volume = st.slider("Volume", 0, 100, 50, key="call_volume")
                st.markdown(f"""
                    <script>
                        setVolume({volume});
                    </script>
                """, unsafe_allow_html=True)
        
        # Call status and notes
        if st.session_state.get('call_active', False):
            st.info("📞 Call in progress...")
            
            # Call notes form
            with st.form("call_notes_form"):
                notes = st.text_area("Call Notes")
                if st.form_submit_button("Save Notes"):
                    if st.session_state.get('current_call_id'):
                        conn = get_db_connection()
                        cur = conn.cursor()
                        cur.execute(
                            "UPDATE phone_calls SET call_notes = %s WHERE id = %s",
                            (notes, st.session_state.current_call_id)
                        )
                        conn.commit()
                        cur.close()
                        conn.close()
                        st.success("Notes saved successfully!")
        
        # Results handling
        st.header("Search Results Management")
        result_found = st.checkbox("Mark as Found")
        
        # Track results from different sources
        source_results = {}
        for source in ["public", "social", "business"]:
            source_results[source] = st.checkbox(f"Found in {source.title()} Records")
        
        if st.button("Save Search"):
            # Overall result is true if any source had results
            overall_result = any(source_results.values())
            add_search_history(
                st.session_state.user_id,
                generated_number,
                overall_result,
                source_results
            )
            st.success("Search saved successfully!")
        
        # Export section
        st.header("Export Data")
        if st.button("Export to Excel"):
            data = {
                'Number': [generated_number],
                'Date': [pd.Timestamp.now()],
                'Result Found': [result_found]
            }
            
            with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp:
                filename = export_to_excel(data, tmp.name)
                
                with open(filename, 'rb') as f:
                    st.download_button(
                        label="Download Excel file",
                        data=f,
                        file_name="search_results.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
    except Exception as e:
        st.error(f"An error occurred while loading the Number Search page: {str(e)}")
        st.error("Please try refreshing the page or contact support if the issue persists.")

if __name__ == "__main__":
    number_search_page()
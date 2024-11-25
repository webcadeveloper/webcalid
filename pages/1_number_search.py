import streamlit as st
import streamlit.components.v1 as components
from scrapers.eoir_scraper import EOIRScraper
import threading
from utils import check_authentication

def number_search_page():
    check_authentication()
    
    # Initialize session state variables
    if 'generated_numbers' not in st.session_state:
        st.session_state.generated_numbers = []
    if 'current_prefix' not in st.session_state:
        st.session_state.current_prefix = 244206
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
            'last_error': None
        }

    st.title("Búsqueda de Números")
    
    # Inject custom CSS and React component
    st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(270deg, #000033, #000066);
    }
    </style>
    """, unsafe_allow_html=True)

    # React Component for Number Generator
    components.html("""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
        .matrix-container {
            background: rgba(0, 0, 0, 0.7);
            padding: 20px;
            border-radius: 10px;
            border: 2px solid #00f;
            margin-bottom: 20px;
        }
        .matrix-number {
            font-size: 2.5rem;
            color: #0f0;
            text-shadow: 0 0 10px #0f0;
            font-family: 'Courier New', monospace;
            margin-bottom: 1rem;
            animation: pulse 1.5s infinite;
        }
        .number-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
            gap: 1rem;
            margin-top: 1rem;
        }
        .number-item {
            background: rgba(0, 0, 0, 0.5);
            padding: 1rem;
            border-radius: 5px;
            border: 1px solid #00f;
            display: flex;
            flex-direction: column;
            align-items: center;
        }
        .copy-button {
            background: #00f;
            color: white;
            border: none;
            padding: 0.5rem 1rem;
            border-radius: 3px;
            cursor: pointer;
            margin-top: 0.5rem;
            transition: all 0.3s ease;
        }
        .copy-button:hover {
            background: #0f0;
            transform: scale(1.05);
        }
        @keyframes pulse {
            0% { opacity: 0.7; }
            50% { opacity: 1; }
            100% { opacity: 0.7; }
        }
        </style>
        <script src="https://unpkg.com/react@17/umd/react.development.js"></script>
        <script src="https://unpkg.com/react-dom@17/umd/react-dom.development.js"></script>
        <script src="https://unpkg.com/babel-standalone@6/babel.min.js"></script>
    </head>
    <body>
        <div id="root"></div>
        <script type="text/babel">
            const NumberGenerator = () => {
                const [currentNumber, setCurrentNumber] = React.useState('244206528');
                const [generatedNumbers, setGeneratedNumbers] = React.useState([]);
                
                const generateNextNumber = () => {
                    const randomSuffix = Math.floor(Math.random() * 900000) + 100000;
                    const newNumber = currentNumber + randomSuffix;
                    setCurrentNumber(newNumber);
                    setGeneratedNumbers([...generatedNumbers, newNumber]);
                };
                
                const copyNumber = (number) => {
                    navigator.clipboard.writeText(number).then(() => {
                        // Use Streamlit's toast notification
                        window.parent.postMessage({
                            type: 'streamlit:showToast',
                            message: `Número ${number} copiado al portapapeles`
                        }, '*');
                    });
                };
                
                return (
                    <div className="matrix-container">
                        <div className="matrix-number">{currentNumber}</div>
                        <button 
                            className="copy-button"
                            onClick={() => generateNextNumber()}
                        >
                            Generar Siguiente
                        </button>
                        <div className="number-grid">
                            {generatedNumbers.map((number, index) => (
                                <div key={index} className="number-item">
                                    <span className="matrix-number">{number}</span>
                                    <button 
                                        className="copy-button"
                                        onClick={() => copyNumber(number)}
                                    >
                                        Copiar
                                    </button>
                                </div>
                            ))}
                        </div>
                    </div>
                );
            };
            
            ReactDOM.render(<NumberGenerator />, document.getElementById('root'));
        </script>
    </body>
    </html>
    """, height=600)

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
        
        def update_progress(progress, number):
            progress_placeholder.progress(progress / 100)
            st.session_state.search_stats.update(scraper.search_stats)
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

    # Add iframes for external searches
    st.header("Búsqueda Externa")
    
    tabs = st.tabs(["EOIR", "Registros Públicos", "Redes Sociales"])
    
    with tabs[0]:
        components.iframe("https://acis.eoir.justice.gov/en/", height=600)
    
    with tabs[1]:
        components.iframe("https://www.whitepages.com", height=600)
    
    with tabs[2]:
        components.iframe("https://www.uscis.gov/es/registros-publicos", height=600)

if __name__ == "__main__":
    number_search_page()

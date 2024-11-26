import streamlit as st
from scrapers.pdl_scraper import PDLScraper
from scrapers.eoir_scraper import EOIRScraper
import pyperclip
import time
import pandas as pd
from datetime import datetime
import json

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
    if 'search_history' not in st.session_state:
        st.session_state.search_history = []

    # Apply matrix style with new success state
    st.markdown("""
    <style>
        .main {
            background-color: #000000;
        }
        .number-display {
            font-family: 'Courier New', Courier, monospace;
            font-size: 2.5rem;
            font-weight: bold;
            color: #0a3a0a;
            text-shadow: 0 0 8px rgba(10, 58, 10, 0.6);
            animation: subtle-glow 2s ease-in-out infinite alternate;
            padding: 1rem;
            margin: 1rem 0;
            background: rgba(10, 58, 10, 0.05);
            border: 2px solid #0a3a0a;
            border-radius: 10px;
        }
        .number-list {
            list-style-type: none;
            padding: 0;
            margin: 1rem 0;
        }
        .number-item {
            font-family: 'Courier New', Courier, monospace;
            color: #0a3a0a;
            text-shadow: 0 0 5px rgba(10, 58, 10, 0.4);
            padding: 0.5rem;
            margin: 0.5rem 0;
            background: rgba(10, 58, 10, 0.03);
            border: 1px solid #0a3a0a;
            border-radius: 5px;
            cursor: pointer;
            transition: all 0.3s ease;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .number-item:hover {
            background: rgba(10, 58, 10, 0.08);
            text-shadow: 0 0 8px rgba(10, 58, 10, 0.5);
        }
        .number-item.success {
            background-color: rgba(255, 0, 0, 0.1);
            border-color: #ff0000;
            color: #ff0000;
        }
        .number-item.success:hover {
            background-color: rgba(255, 0, 0, 0.15);
        }
        .source-indicator {
            font-size: 0.8em;
            padding: 0.2em 0.5em;
            border-radius: 3px;
            margin-left: 0.5em;
        }
        .pdl-source {
            background-color: rgba(0, 255, 0, 0.1);
            color: #00ff00;
        }
        .eoir-source {
            background-color: rgba(255, 165, 0, 0.1);
            color: #ffa500;
        }
        @keyframes subtle-glow {
            from {
                text-shadow: 0 0 3px rgba(10, 58, 10, 0.4),
                            0 0 5px rgba(10, 58, 10, 0.3);
            }
            to {
                text-shadow: 0 0 5px rgba(10, 58, 10, 0.5),
                            0 0 8px rgba(10, 58, 10, 0.4);
            }
        }
        .tooltip {
            position: relative;
            display: inline-block;
        }
        .tooltip .tooltiptext {
            visibility: hidden;
            width: 200px;
            background-color: rgba(0, 0, 0, 0.9);
            color: #fff;
            text-align: center;
            border-radius: 6px;
            padding: 5px;
            position: absolute;
            z-index: 1;
            bottom: 125%;
            left: 50%;
            margin-left: -100px;
            opacity: 0;
            transition: opacity 0.3s;
        }
        .tooltip:hover .tooltiptext {
            visibility: visible;
            opacity: 1;
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
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("Generar Siguiente Número"):
            new_number = str(st.session_state.current_prefix * 1000 + len(st.session_state.generated_numbers)).zfill(9)
            st.session_state.generated_numbers.append(new_number)
            st.session_state.current_prefix += 1

            # Initialize search result
            search_result = {
                'number': new_number,
                'timestamp': datetime.now().isoformat(),
                'pdl_found': False,
                'eoir_found': False,
                'pdl_data': None,
                'eoir_data': None
            }

            # PDL API Integration
            pdl_scraper = PDLScraper()
            eoir_scraper = EOIRScraper()
            
            # Check PDL API
            if st.session_state.get('pdl_api_key'):
                pdl_scraper.api_key = st.session_state.pdl_api_key
                pdl_result = pdl_scraper.search(new_number)
                if pdl_result['status'] == 'success':
                    search_result['pdl_found'] = True
                    search_result['pdl_data'] = pdl_result['data']
                    st.success("¡Número encontrado en PDL!")
                    st.json(pdl_result['data'])

            # Check EOIR system
            with st.spinner("Verificando en sistema EOIR..."):
                eoir_result = eoir_scraper.search(new_number)
                if eoir_result['status'] == 'success':
                    search_result['eoir_found'] = True
                    search_result['eoir_data'] = eoir_result['data']
                    st.success("¡Caso encontrado en EOIR!")
                    st.markdown("""
                        <div class="eoir-result matrix-theme">
                            <h3>Información del Caso EOIR</h3>
                        </div>
                    """, unsafe_allow_html=True)
                    st.json(eoir_result['data'])
                elif eoir_result['status'] == 'not_found':
                    st.info("No se encontró el caso en EOIR")
                else:
                    st.error(f"Error al buscar en EOIR: {eoir_result.get('error', 'Error desconocido')}")

            # Add to search history
            st.session_state.search_history.append(search_result)

    with col2:
        if st.button("Copiar Último Número") and st.session_state.generated_numbers:
            pyperclip.copy(st.session_state.generated_numbers[-1])
            st.success("¡Número copiado al portapapeles!")

    with col3:
        if st.button("Exportar Reporte"):
            if st.session_state.search_history:
                df = pd.DataFrame([{
                    'Número': item['number'],
                    'Fecha': item['timestamp'],
                    'Encontrado PDL': item['pdl_found'],
                    'Encontrado EOIR': item['eoir_found'],
                    'Fuentes': 'PDL' if item['pdl_found'] else '' + 
                             ('EOIR' if item['eoir_found'] else '')
                } for item in st.session_state.search_history])
                
                csv = df.to_csv(index=False)
                st.download_button(
                    label="Descargar Reporte CSV",
                    data=csv,
                    file_name=f"reporte_numeros_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )

    # Display search history with enhanced visualization
    if st.session_state.search_history:
        st.markdown("<h3>Historial de Búsquedas</h3>", unsafe_allow_html=True)
        
        for item in reversed(st.session_state.search_history):
            success_class = "success" if item['pdl_found'] or item['eoir_found'] else ""
            tooltip_text = f"""
                Fecha: {item['timestamp']}
                PDL: {'Encontrado' if item['pdl_found'] else 'No encontrado'}
                EOIR: {'Encontrado' if item['eoir_found'] else 'No encontrado'}
            """
            
            source_indicators = []
            if item['pdl_found']:
                source_indicators.append('<span class="source-indicator pdl-source">PDL</span>')
            if item['eoir_found']:
                source_indicators.append('<span class="source-indicator eoir-source">EOIR</span>')
            
            source_html = ''.join(source_indicators)
            
            st.markdown(f"""
                <div class="number-item {success_class} tooltip" onclick="navigator.clipboard.writeText('{item['number']}')">
                    <span>{item['number']}</span>
                    <div>
                        {source_html}
                        <span class="tooltiptext">{tooltip_text}</span>
                    </div>
                </div>
            """, unsafe_allow_html=True)

if __name__ == "__main__":
    page_render()

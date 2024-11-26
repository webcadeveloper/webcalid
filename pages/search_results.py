import streamlit as st
from scrapers.pdl_scraper import PDLScraper
from scrapers.eoir_scraper import EOIRScraper
import pandas as pd
from datetime import datetime
import json

def page_render():
    if not st.session_state.get('user_id'):
        st.warning("Por favor inicie sesión")
        st.stop()
        return

    # Apply matrix style
    st.markdown("""
    <style>
        .main {
            background-color: #000000;
        }
        .number-panel {
            font-family: 'Courier New', Courier, monospace;
            font-size: 2.5rem;
            font-weight: bold;
            color: #0a3a0a;
            text-shadow: 0 0 8px rgba(10, 58, 10, 0.6);
            padding: 1rem;
            margin: 1rem 0;
            background: rgba(10, 58, 10, 0.05);
            border: 2px solid #0a3a0a;
            border-radius: 10px;
            text-align: center;
        }
        .result-section {
            background: rgba(0, 0, 0, 0.8);
            border: 1px solid #0a3a0a;
            border-radius: 8px;
            padding: 1rem;
            margin: 1rem 0;
        }
        .result-section.found {
            border-color: #ff0000;
            background: rgba(255, 0, 0, 0.1);
        }
        .source-badge {
            display: inline-block;
            padding: 0.2rem 0.5rem;
            border-radius: 4px;
            font-size: 0.8rem;
            margin: 0 0.2rem;
        }
        .pdl-badge {
            background: rgba(0, 255, 0, 0.1);
            color: #00ff00;
            border: 1px solid #00ff00;
        }
        .eoir-badge {
            background: rgba(255, 0, 0, 0.1);
            color: #ff0000;
            border: 1px solid #ff0000;
        }
        .copy-button {
            background: rgba(10, 58, 10, 0.1);
            color: #0a3a0a;
            border: 1px solid #0a3a0a;
            padding: 0.3rem 0.6rem;
            border-radius: 4px;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        .copy-button:hover {
            background: rgba(10, 58, 10, 0.2);
        }
        .history-item {
            padding: 0.5rem;
            margin: 0.5rem 0;
            border: 1px solid #0a3a0a;
            border-radius: 4px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .history-item.found {
            border-color: #ff0000;
            background: rgba(255, 0, 0, 0.05);
        }
    </style>
    """, unsafe_allow_html=True)

    st.title("Resultados de Búsqueda")

    # Current number display
    if 'current_number' in st.session_state:
        st.markdown(f'<div class="number-panel">{st.session_state.current_number}</div>', 
                   unsafe_allow_html=True)

    # Results sections
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Resultados PDL")
        if 'pdl_results' in st.session_state:
            with st.container():
                success_class = " found" if st.session_state.pdl_results.get('status') == 'success' else ""
                st.markdown(f'<div class="result-section{success_class}">', unsafe_allow_html=True)
                if st.session_state.pdl_results.get('status') == 'success':
                    st.json(st.session_state.pdl_results.get('data', {}))
                else:
                    st.write("No se encontraron resultados en PDL")
                st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.subheader("Resultados EOIR")
        if 'eoir_results' in st.session_state:
            with st.container():
                success_class = " found" if st.session_state.eoir_results.get('status') == 'success' else ""
                st.markdown(f'<div class="result-section{success_class}">', unsafe_allow_html=True)
                if st.session_state.eoir_results.get('status') == 'success':
                    st.json(st.session_state.eoir_results.get('data', {}))
                else:
                    st.write("No se encontraron resultados en EOIR")
                st.markdown('</div>', unsafe_allow_html=True)

    # Export section
    st.subheader("Exportar Resultados")
    if st.button("Exportar Reporte"):
        if 'search_history' in st.session_state and st.session_state.search_history:
            df = pd.DataFrame([{
                'Número': item['number'],
                'Fecha': item['timestamp'],
                'PDL Encontrado': item['pdl_found'],
                'EOIR Encontrado': item['eoir_found'],
                'Fuentes': ('PDL ' if item['pdl_found'] else '') + 
                          ('EOIR' if item['eoir_found'] else '')
            } for item in st.session_state.search_history])
            
            csv = df.to_csv(index=False)
            st.download_button(
                label="Descargar Reporte CSV",
                data=csv,
                file_name=f"reporte_busquedas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )

    # Search history
    st.subheader("Historial de Búsquedas")
    if 'search_history' in st.session_state:
        for item in reversed(st.session_state.search_history):
            success_class = " found" if item['pdl_found'] or item['eoir_found'] else ""
            st.markdown(f"""
                <div class="history-item{success_class}">
                    <span>{item['number']}</span>
                    <div>
                        {f'<span class="source-badge pdl-badge">PDL</span>' if item['pdl_found'] else ''}
                        {f'<span class="source-badge eoir-badge">EOIR</span>' if item['eoir_found'] else ''}
                        <button class="copy-button" onclick="navigator.clipboard.writeText('{item['number']}')">
                            Copiar
                        </button>
                    </div>
                </div>
            """, unsafe_allow_html=True)

if __name__ == "__main__":
    page_render()

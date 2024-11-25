import streamlit as st
import random
from utils import check_authentication

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

def number_search_page():
    check_authentication()
    
    st.title("Búsqueda por Número")
    
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
    
    # Display generated numbers list
    if st.session_state.generated_numbers:
        st.header("Números Generados")
        for number in reversed(st.session_state.generated_numbers[-10:]):  # Show last 10 numbers
            st.markdown(f"""
            <div style="font-family: 'Courier New'; color: #00ff00; text-shadow: 0 0 3px #00ff00; 
                        padding: 0.5rem; font-size: 1.2rem;">
                {number}
            </div>
            """, unsafe_allow_html=True)
    
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

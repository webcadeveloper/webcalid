import streamlit as st
import pandas as pd
from utils import generate_sequential_number, generate_random_number, export_to_excel, check_authentication
from database import add_search_history
import tempfile

def number_search_page():
    check_authentication()
    
    st.title("Number Search")
    
    # Number generation section
    st.header("Generate Number")
    col1, col2 = st.columns(2)
    
    with col1:
        generation_method = st.radio(
            "Number Generation Method",
            ["Sequential", "Random"]
        )
    
    with col2:
        if generation_method == "Sequential":
            start_number = st.number_input("Start From", min_value=0, value=0)
            generated_number = generate_sequential_number(start_number)
        else:
            generated_number = generate_random_number()
            if st.button("Generate New Random Number"):
                generated_number = generate_random_number()
    
    st.subheader("Generated Number:")
    st.write(generated_number)
    
    # Search section
    st.header("Search Results")
    
    # Create tabs for different data sources
    tab1, tab2, tab3 = st.tabs(["Source 1", "Source 2", "Source 3"])
    
    with tab1:
        st.markdown(f"""
        <iframe
            src="about:blank"
            width="100%"
            height="400"
            style="border: 1px solid #ccc;"
        ></iframe>
        """, unsafe_allow_html=True)
    
    with tab2:
        st.markdown(f"""
        <iframe
            src="about:blank"
            width="100%"
            height="400"
            style="border: 1px solid #ccc;"
        ></iframe>
        """, unsafe_allow_html=True)
    
    with tab3:
        st.markdown(f"""
        <iframe
            src="about:blank"
            width="100%"
            height="400"
            style="border: 1px solid #ccc;"
        ></iframe>
        """, unsafe_allow_html=True)
    
    # Results handling
    st.header("Search Results Management")
    result_found = st.checkbox("Mark as Found")
    
    if st.button("Save Search"):
        add_search_history(
            st.session_state.user_id,
            generated_number,
            result_found
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

if __name__ == "__main__":
    number_search_page()

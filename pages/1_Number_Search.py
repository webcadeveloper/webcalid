import streamlit as st
import pandas as pd
from utils import generate_sequential_number, generate_random_number, export_to_excel, check_authentication
from database import add_search_history
import tempfile

def number_search_page():
    check_authentication()
    
    st.title("Number Search")
    
    # Add error handling for page routing
    try:
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
        tab1, tab2, tab3 = st.tabs(["Public Records", "Social Media", "Business Records"])
        
        # Function to generate URLs based on number
        def get_search_urls(number):
            return {
                "public": f"https://www.example.com/public-records?q={number}",
                "social": f"https://www.example.com/social-search?id={number}",
                "business": f"https://www.example.com/business-lookup?ref={number}"
            }
        
        # Generate URLs for the current number
        search_urls = get_search_urls(generated_number)
        
        # Helper function to create iframe with loading state
        def create_iframe_with_loading(url, source_name):
            with st.spinner(f"Loading {source_name} data..."):
                try:
                    components_container = st.container()
                    with components_container:
                        st.markdown(f"""
                        <div style="border: 1px solid #ccc; padding: 10px;">
                            <iframe
                                src="{url}"
                                width="100%"
                                height="400"
                                style="border: none;"
                            ></iframe>
                        </div>
                        """, unsafe_allow_html=True)
                        with st.expander(f"{source_name} Error"):
                            st.error(f"If the {source_name} content fails to load, please refresh the page.")
                except Exception as e:
                    st.error(f"Error loading {source_name}: {str(e)}")
        
        with tab1:
            create_iframe_with_loading(search_urls["public"], "Public Records")
        
        with tab2:
            create_iframe_with_loading(search_urls["social"], "Social Media")
        
        with tab3:
            create_iframe_with_loading(search_urls["business"], "Business Records")
        
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

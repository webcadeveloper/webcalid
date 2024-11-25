import streamlit as st
import pandas as pd
from utils import generate_sequential_number, generate_random_number, export_to_excel, check_authentication
from database import add_search_history, get_db_connection, add_phone_call
import json
import tempfile

def number_search_page():
    check_authentication()
    
    # Add custom CSS for matrix effect and styling
    st.markdown("""
    <style>
        /* Matrix effect and general styling */
        .matrix-number {
            font-family: 'Courier New', monospace;
            font-size: 2rem;
            font-weight: bold;
            color: #0f0;
            text-shadow: 0 0 15px #0f0;
            animation: matrix 1.5s linear infinite;
            padding: 1rem;
            background: rgba(0, 0, 0, 0.6);
            border: 2px solid #00f;
            border-radius: 10px;
            margin-bottom: 1rem;
        }
        
        .iframe-container {
            background: rgba(0, 0, 0, 0.6);
            border: 2px solid #00f;
            border-radius: 10px;
            padding: 1rem;
            margin: 1rem 0;
        }
        
        .number-list {
            list-style-type: none;
            padding: 0;
            color: #0f0;
            text-shadow: 0 0 10px #0f0;
            font-size: 1.2rem;
        }
        
        .number-list li {
            margin: 0.5rem 0;
            cursor: pointer;
            transition: color 0.3s, text-shadow 0.3s;
        }
        
        .number-list li:hover {
            color: #0ff;
            text-shadow: 0 0 20px #0ff;
        }
        
        @keyframes matrix {
            0% { opacity: 0.1; }
            50% { opacity: 1; }
            100% { opacity: 0.1; }
        }
        
        /* Style improvements for iframes */
        iframe {
            border: 2px solid #00f !important;
            background: rgba(0, 0, 0, 0.8) !important;
            border-radius: 5px !important;
        }
        
        /* Button styling */
        .stButton > button {
            background-color: #00f !important;
            color: white !important;
            border: 2px solid #00f !important;
            border-radius: 5px !important;
            transition: all 0.3s !important;
        }
        
        .stButton > button:hover {
            background-color: #0f0 !important;
            border-color: #0f0 !important;
            color: black !important;
        }
    </style>
    """, unsafe_allow_html=True)
    
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
        st.markdown(f"""
            <div class="matrix-number" onclick="navigator.clipboard.writeText('{generated_number}')" 
                 title="Click to copy">
                {generated_number}
            </div>
            <script>
                const number = document.querySelector('.matrix-number');
                number.addEventListener('click', async () => {{
                    await navigator.clipboard.writeText('{generated_number}');
                    number.style.color = '#0ff';
                    setTimeout(() => number.style.color = '#0f0', 500);
                }});
            </script>
        """, unsafe_allow_html=True)
        
        # Add copy button with visual feedback
        if st.button("📋 Copy Number"):
            st.success("Number copied to clipboard!")
        
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
                        <div class="iframe-container">
                            <iframe
                                src="{url}"
                                width="100%"
                                height="400"
                                style="border: none;"
                            ></iframe>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Add confirmation button for the source
                        col1, col2 = st.columns([3, 1])
                        with col2:
                            if st.button(f"✓ Confirm {source_name}"):
                                st.success(f"{source_name} data confirmed!")
                except Exception as e:
                    st.error(f"Error loading {source_name}: {str(e)}")
        
        with tab1:
            create_iframe_with_loading(search_urls["public"], "Public Records")
        
        with tab2:
            create_iframe_with_loading(search_urls["social"], "Social Media")
        
        with tab3:
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

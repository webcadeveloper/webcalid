import streamlit as st
from utils.phone_call import PhoneCallPage
from utils.auth_utils import check_authentication

def page_render():
    # Check authentication
    if not st.session_state.get('user_id'):
        st.warning("Por favor inicie sesión")
        st.stop()
        return
        
    # Initialize and render phone call page
    phone_page = PhoneCallPage()
    phone_page.render()

if __name__ == "__main__":
    page_render()

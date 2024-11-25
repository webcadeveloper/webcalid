import random
import pandas as pd
import streamlit as st
from datetime import datetime
import hashlib

def generate_sequential_number(start_from):
    return str(start_from + 1).zfill(8)

def generate_random_number():
    return str(random.randint(10000000, 99999999))

def export_to_excel(data, filename):
    df = pd.DataFrame(data)
    buffer = pd.ExcelWriter(filename, engine='openpyxl')
    df.to_excel(buffer, index=False)
    buffer.close()
    return filename

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(stored_password, provided_password):
    return stored_password == hash_password(provided_password)

def check_authentication():
    if 'user_id' not in st.session_state:
        st.warning("Please log in to access this page")
        st.stop()

def check_supervisor():
    if 'is_supervisor' not in st.session_state or not st.session_state.is_supervisor:
        st.error("Access denied. Supervisor privileges required.")
        st.stop()

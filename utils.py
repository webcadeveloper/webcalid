import random
import pandas as pd
import streamlit as st
from datetime import datetime
import hashlib

def generate_sequential_number(start_from):
    """Generate a 9-digit sequential number with leading zeros if needed"""
    return str(start_from + 1).zfill(9)

def generate_random_number():
    """Generate a random 9-digit number between 000000000 and 999999999"""
    return str(random.randint(0, 999999999)).zfill(9)

def export_to_excel(data, filename):
    df = pd.DataFrame(data)
    buffer = pd.ExcelWriter(filename, engine='openpyxl')
    df.to_excel(buffer, index=False)
    buffer.close()
    return filename

# Authentication functions moved to utils/auth_utils.py
from utils.auth_utils import hash_password, verify_password

def check_authentication():
    if 'user_id' not in st.session_state:
        st.warning("Please log in to access this page")
        st.stop()

def check_supervisor():
    if 'is_supervisor' not in st.session_state or not st.session_state.is_supervisor:
        st.error("Access denied. Supervisor privileges required.")
        st.stop()

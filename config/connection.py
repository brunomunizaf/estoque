from supabase import create_client
import os
import streamlit as st

# Get Supabase credentials from environment variables
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not all([SUPABASE_URL, SUPABASE_KEY]):
    st.error("Missing required Supabase environment variables. Please set SUPABASE_URL and SUPABASE_KEY.")
    st.stop()

try:
    # Initialize Supabase client
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    # Test the connection
    response = supabase.table('items').select("*").limit(1).execute()
    
    # Create a function to get the client
    def get_supabase_client():
        return supabase
        
except Exception as e:
    st.error(f"Failed to connect to Supabase: {str(e)}")
    st.stop()
from supabase import create_client
import os

# Configurações do Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Missing required Supabase environment variables. Please set SUPABASE_URL and SUPABASE_KEY.")

# Criar cliente Supabase
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def get_supabase_client():
    """
    Retorna o cliente Supabase configurado
    """
    return supabase 
from config.supabase_config import get_supabase_client

def get_all_products():
    """
    Retorna todos os produtos do banco de dados
    """
    supabase = get_supabase_client()
    response = supabase.table('products').select("*").execute()
    return response.data

def add_product(name, description, price, quantity):
    """
    Adiciona um novo produto ao banco de dados
    """
    supabase = get_supabase_client()
    data = {
        'name': name,
        'description': description,
        'price': price,
        'quantity': quantity
    }
    response = supabase.table('products').insert(data).execute()
    return response.data

def update_product_quantity(product_id, new_quantity):
    """
    Atualiza a quantidade de um produto
    """
    supabase = get_supabase_client()
    response = supabase.table('products').update({'quantity': new_quantity}).eq('id', product_id).execute()
    return response.data

def delete_product(product_id):
    """
    Remove um produto do banco de dados
    """
    supabase = get_supabase_client()
    response = supabase.table('products').delete().eq('id', product_id).execute()
    return response.data 
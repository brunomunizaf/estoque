import pandas as pd
import streamlit as st
from config.connection import get_supabase_client
import pytz
from datetime import datetime

def carregar_dados():
    supabase = get_supabase_client()
    
    # Carregar items
    items_response = supabase.table('items').select("*").execute()
    items_df = pd.DataFrame(items_response.data)
    
    # Carregar transações
    transactions_response = supabase.table('transactions').select("*").execute()
    transactions_df = pd.DataFrame(transactions_response.data)
    
    # Ensure required columns exist in items
    if not all(col in items_df.columns for col in ['id', 'name', 'unit']):
        st.error("Items table is missing required columns: id, name, unit")
        st.stop()
    
    # Only check transaction columns if there are transactions
    if not transactions_df.empty:
        if not all(col in transactions_df.columns for col in ['item', 'amount', 'transaction_type']):
            st.error("Transactions table is missing required columns: item, amount, transaction_type")
            st.stop()
    
    return items_df, transactions_df

def mostrar_estoque(df, transactions_df=None):
    if transactions_df is not None:
        saldo_df = calcular_saldo(df, transactions_df)
        # Renomear colunas para português
        colunas_pt = {
            "name": "Nome",
            "unit": "Unidade",
            "Saldo Atual": "Saldo Atual"
        }
        saldo_df = saldo_df.rename(columns=colunas_pt)
        st.dataframe(saldo_df[["Nome", "Unidade", "Saldo Atual"]], use_container_width=True)
    else:
        # Renomear colunas para português
        colunas_pt = {
            "name": "Nome",
            "unit": "Unidade"
        }
        df = df.rename(columns=colunas_pt)
        st.dataframe(df[["Nome", "Unidade"]], use_container_width=True)

def mostrar_movimentacoes(df):
    if not df.empty:
        # Get items data to join with transactions
        supabase = get_supabase_client()
        items_response = supabase.table('items').select("id,name").execute()
        items_df = pd.DataFrame(items_response.data)
        
        # Join transactions with items to get names
        df = pd.merge(df, items_df, left_on="item", right_on="id", how="left")
        
        # Convert timestamp to datetime and format for display
        df['timestamp'] = pd.to_datetime(df['timestamp'], format='ISO8601')
        
        # Sort transactions by timestamp in descending order
        df = df.sort_values(by="timestamp", ascending=False)
        
        # Display only the last 10 most recent transactions
        df = df.head(10)
        
        df['timestamp'] = df['timestamp'].dt.strftime("%d/%m/%Y %H:%M:%S")
        
        # Verificar quais colunas existem no DataFrame
        colunas_disponiveis = df.columns.tolist()
        
        # Mapear colunas originais para português
        colunas_pt = {
            "timestamp": "Data/Hora",
            "amount": "Quantidade",
            "name": "Nome do Item",
            "transaction_type": "Tipo de Movimentação",
            "observation": "Observação"
        }
        
        # Filtrar apenas as colunas que existem
        colunas_pt = {k: v for k, v in colunas_pt.items() if k in colunas_disponiveis}
        
        # Renomear colunas
        df = df.rename(columns=colunas_pt)
        
        # Mostrar apenas as colunas renomeadas
        st.dataframe(df[list(colunas_pt.values())], use_container_width=True)
    else:
        st.write("Nenhuma movimentação encontrada.")

def criar_movimentacao(item_id, quantidade, tipo, observacao=None):
    supabase = get_supabase_client()
    
    # Create transaction with ISO format timestamp
    transaction_data = {
        "item": item_id,
        "amount": quantidade if tipo == "Entrada" else -quantidade,
        "transaction_type": tipo,
        "observation": observacao,
        "timestamp": datetime.now(pytz.timezone('America/Sao_Paulo')).isoformat()
    }
    
    supabase.table('transactions').insert(transaction_data).execute()

def calcular_saldo(items_df, transactions_df):
    if transactions_df.empty:
        items_df["Saldo Atual"] = 0
        return items_df
    
    # Calculate total transactions per item
    saldo = transactions_df.groupby("item")["amount"].sum().reset_index()
    
    # Merge with items using 'id' from items and 'item' from transactions
    result = pd.merge(items_df, saldo, left_on="id", right_on="item", how="left")
    result["Saldo Atual"] = result["amount"].fillna(0)
    
    # Drop the temporary 'item' column used for merging
    if "item" in result.columns:
        result = result.drop(columns=["item"])
    
    return result

def preparar_dados_grafico(items_df, transactions_df, selected_item_id=None):
    if transactions_df.empty:
        return pd.DataFrame()
    
    # Convert timestamp to datetime
    transactions_df['timestamp'] = pd.to_datetime(transactions_df['timestamp'])
    
    # Merge transactions with items to get names
    df = pd.merge(transactions_df, items_df[['id', 'name']], left_on='item', right_on='id', how='left')
    
    # Filter for the selected item if provided
    if selected_item_id is not None:
        df = df[df['item'] == selected_item_id]
    
    # Calculate cumulative sum for each item
    df = df.sort_values('timestamp')
    df['cumulative_amount'] = df.groupby('item')['amount'].cumsum()
    
    # Aggregate data by day
    df['date'] = df['timestamp'].dt.date
    df = df.groupby(['date', 'name'])['cumulative_amount'].last().reset_index()
    
    # Create a pivot table with date as index and items as columns
    pivot_df = df.pivot_table(
        index='date',
        columns='name',
        values='cumulative_amount',
        aggfunc='last'
    ).fillna(method='ffill')
    
    # Ensure all items from the selected sector are included
    if selected_item_id is None:
        all_items = items_df['name'].tolist()
        for item in all_items:
            if item not in pivot_df.columns:
                pivot_df[item] = 0
    
    return pivot_df
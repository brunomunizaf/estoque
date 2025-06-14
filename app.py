import streamlit as st
from utils.estoque_utils import carregar_dados, mostrar_estoque, mostrar_movimentacoes, criar_movimentacao, calcular_saldo
from fpdf import FPDF
import io
from datetime import datetime
import pytz
import pandas as pd
import os

def gerar_pdf(transacoes_hoje, relatorio):
    pdf = FPDF(orientation='L')  # Set landscape orientation
    pdf.add_page()
    
    # Get page width (now using landscape dimensions)
    page_width = pdf.w - 2 * pdf.l_margin
    
    # Use built-in font instead of Arial
    pdf.set_font("Helvetica", style="B", size=12)
    
    # Movimentações do Dia primeiro
    pdf.cell(page_width, 10, txt="Movimentações do Dia", ln=True, align="C")
    pdf.ln(5)
    pdf.set_font("Helvetica", style="B", size=12)
    
    # Calculate column widths based on page width
    col_widths = {
        "Data/Hora": page_width * 0.2,
        "Quantidade": page_width * 0.15,
        "Nome do Item": page_width * 0.3,
        "Tipo": page_width * 0.15,
        "Observação": page_width * 0.2
    }
    
    # Draw header
    pdf.cell(col_widths["Data/Hora"], 10, "Data/Hora", border=1, align="C")
    pdf.cell(col_widths["Quantidade"], 10, "Quantidade", border=1, align="C")
    pdf.cell(col_widths["Nome do Item"], 10, "Nome do Item", border=1, align="C")
    pdf.cell(col_widths["Tipo"], 10, "Tipo", border=1, align="C")
    pdf.cell(col_widths["Observação"], 10, "Observação", border=1, align="C", ln=True)
    
    pdf.set_font("Helvetica", size=12)
    # Sort transactions in reverse order (most recent first)
    for _, row in transacoes_hoje.sort_values(by="Data/Hora", ascending=False).iterrows():
        # Clean and encode text to handle special characters
        data_hora = str(row["Data/Hora"]).encode('latin1', 'replace').decode('latin1')
        quantidade = str(row["Quantidade"]).encode('latin1', 'replace').decode('latin1')
        nome_item = str(row["Nome do Item"])[0:30].encode('latin1', 'replace').decode('latin1')
        tipo = str(row["Tipo de Movimentação"]).encode('latin1', 'replace').decode('latin1')
        obs = str(row.get("Observação", ""))[0:30].encode('latin1', 'replace').decode('latin1')
        
        pdf.cell(col_widths["Data/Hora"], 10, data_hora, border=1, align="C")
        pdf.cell(col_widths["Quantidade"], 10, quantidade, border=1, align="C")
        pdf.cell(col_widths["Nome do Item"], 10, nome_item, border=1, align="C")
        pdf.cell(col_widths["Tipo"], 10, tipo, border=1, align="C")
        pdf.cell(col_widths["Observação"], 10, obs, border=1, align="C", ln=True)
    
    pdf.ln(10)
    
    # Estoque Atual depois
    pdf.set_font("Helvetica", style="B", size=12)
    pdf.cell(page_width, 10, txt="Relatório Diário de Estoque", ln=True, align="C")
    pdf.ln(5)
    
    # Calculate column widths for stock report
    stock_col_widths = {
        "Nome": page_width * 0.5,
        "Unidade": page_width * 0.25,
        "Saldo Atual": page_width * 0.25
    }
    
    # Draw header
    pdf.cell(stock_col_widths["Nome"], 10, "Nome", border=1, align="C")
    pdf.cell(stock_col_widths["Unidade"], 10, "Unidade", border=1, align="C")
    pdf.cell(stock_col_widths["Saldo Atual"], 10, "Saldo Atual", border=1, align="C", ln=True)
    
    pdf.set_font("Helvetica", size=12)
    # Group items by section
    for section, group in relatorio.groupby("Setor"):
        # Add section header
        pdf.set_font("Helvetica", style="B", size=12)
        pdf.cell(page_width, 10, f"Setor: {section}", ln=True)
        pdf.set_font("Helvetica", size=12)
        
        for _, row in group.iterrows():
            # Clean and encode text to handle special characters
            nome = str(row["Nome"]).encode('latin1', 'replace').decode('latin1')
            unidade = str(row["Unidade"]).encode('latin1', 'replace').decode('latin1')
            saldo = str(row["Saldo Atual"]).encode('latin1', 'replace').decode('latin1')
            
            pdf.cell(stock_col_widths["Nome"], 10, nome, border=1, align="C")
            pdf.cell(stock_col_widths["Unidade"], 10, unidade, border=1, align="C")
            pdf.cell(stock_col_widths["Saldo Atual"], 10, saldo, border=1, align="C", ln=True)
        
        pdf.ln(5)  # Add some space between sections
    
    pdf_bytes = pdf.output(dest='S').encode('latin1')
    pdf_buffer = io.BytesIO(pdf_bytes)
    return pdf_buffer

def main():
    st.title("Touché | Estoque")
    
    # Setores disponíveis (first)
    setores = ["Todos", "Serigrafia", "Cola", "Outros", "Papéis", "Papelão"]
    setor = st.selectbox("Selecione o setor para visualizar:", setores)

    # Carregar dados
    items_df, transactions_df = carregar_dados()

    # Filtrar visualização pelo setor
    if setor != "Todos":
        items_df = items_df[items_df["sector"] == setor]
        item_ids = set(items_df["id"])
        transactions_df = transactions_df[transactions_df["item"].isin(item_ids)]

    # Formulário para nova movimentação (after dropdown)
    st.header("Registrar Movimentação")
    with st.form("nova_movimentacao"):
        item_options = {row["name"]: row["id"] for _, row in items_df.iterrows()}
        item_nome = st.selectbox("Item", list(item_options.keys()))
        tipo = st.radio("Tipo de Movimentação", ["Entrada", "Saída"])
        quantidade = st.number_input("Quantidade", min_value=1, step=1)
        observacao = st.text_input("Observação (opcional)")
        submitted = st.form_submit_button("Registrar")
        if submitted:
            criar_movimentacao(item_options[item_nome], quantidade, tipo, observacao)
            st.success("Movimentação registrada com sucesso!")
            # Recarregar dados após inserção e re-filtrar
            items_df, transactions_df = carregar_dados()
            if setor != "Todos":
                items_df = items_df[items_df["sector"] == setor]
                item_ids = set(items_df["id"])
                transactions_df = transactions_df[transactions_df["item"].isin(item_ids)]

    mostrar_estoque(items_df, transactions_df)
    mostrar_movimentacoes(transactions_df)

    # Exportar relatório diário em PDF (bottom)
    st.header("Exportar Relatório Diário")
    # Carregar dados novamente sem filtro para o relatório
    items_df_full, transactions_df_full = carregar_dados()
    saldo_df = calcular_saldo(items_df_full, transactions_df_full)
    relatorio = saldo_df[["name", "unit", "Saldo Atual", "sector"]].rename(columns={
        "name": "Nome", 
        "unit": "Unidade",
        "sector": "Setor"
    })
    
    # Initialize empty DataFrame for transactions if none exist
    if transactions_df_full.empty:
        transacoes_hoje = pd.DataFrame(columns=["Data/Hora", "Quantidade", "Nome do Item", "Tipo de Movimentação", "Observação"])
    else:
        # Join transactions with items to get names for the report
        transactions_df_full = pd.merge(transactions_df_full, items_df_full[["id", "name"]], left_on="item", right_on="id", how="left")
        
        # Renomear colunas para português antes de filtrar transações do dia
        colunas_pt = {
            "timestamp": "Data/Hora",
            "amount": "Quantidade",
            "name": "Nome do Item",
            "transaction_type": "Tipo de Movimentação",
            "observation": "Observação"
        }
        transacoes_hoje = transactions_df_full.rename(columns=colunas_pt).copy()
        
        # Filtrar transações do dia atual
        hoje = datetime.now(pytz.timezone('America/Sao_Paulo')).date()
        transacoes_hoje["Data/Hora"] = pd.to_datetime(transacoes_hoje["Data/Hora"], format='ISO8601')
        transacoes_hoje = transacoes_hoje[transacoes_hoje["Data/Hora"].dt.date == hoje]
        transacoes_hoje["Data/Hora"] = transacoes_hoje["Data/Hora"].dt.strftime("%d/%m/%Y %H:%M:%S")
    
    pdf_buffer = gerar_pdf(transacoes_hoje, relatorio)
    now_str = datetime.now().strftime("%Y-%m-%d_%H-%M")
    st.download_button(
        label="Exportar PDF do Estoque Atual",
        data=pdf_buffer,
        file_name=f"relatorio_estoque_{now_str}.pdf",
        mime="application/pdf"
    )

if __name__ == "__main__":
    main() 
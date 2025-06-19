import streamlit as st
from utils.estoque_utils import carregar_dados, mostrar_estoque, mostrar_movimentacoes, criar_movimentacao, calcular_saldo, preparar_dados_grafico
from fpdf import FPDF
import io
from datetime import datetime
import pytz
import pandas as pd
import os
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from streamlit_echarts import st_echarts

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
    
    # Initialize session state for selected sector
    if 'selected_sector' not in st.session_state:
        st.session_state.selected_sector = "Todos"
    
    # Add CSS to ensure equal spacing
    st.markdown("""
        <style>
        .stButton {
            width: 100%;
            display: flex;
            justify-content: center;
        }
        .stButton > button {
            width: 100%;
            padding-left: 1rem;
            padding-right: 1rem;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Create buttons for each sector with equal spacing
    col1, col2, col3, col4, col5, col6 = st.columns([1, 1, 1, 1, 1, 1])
    
    with col1:
        if st.button("Todos", type="primary" if st.session_state.selected_sector == "Todos" else "secondary", use_container_width=True):
            st.session_state.selected_sector = "Todos"
            st.rerun()
    with col2:
        if st.button("Serigrafia", type="primary" if st.session_state.selected_sector == "Serigrafia" else "secondary", use_container_width=True):
            st.session_state.selected_sector = "Serigrafia"
            st.rerun()
    with col3:
        if st.button("Papelão", type="primary" if st.session_state.selected_sector == "Papelão" else "secondary", use_container_width=True):
            st.session_state.selected_sector = "Papelão"
            st.rerun()
    with col4:
        if st.button("Papéis", type="primary" if st.session_state.selected_sector == "Papéis" else "secondary", use_container_width=True):
            st.session_state.selected_sector = "Papéis"
            st.rerun()
    with col5:
        if st.button("Cola", type="primary" if st.session_state.selected_sector == "Cola" else "secondary", use_container_width=True):
            st.session_state.selected_sector = "Cola"
            st.rerun()        
    with col6:
        if st.button("Outros", type="primary" if st.session_state.selected_sector == "Outros" else "secondary", use_container_width=True):
            st.session_state.selected_sector = "Outros"
            st.rerun()
    
    setor = st.session_state.selected_sector

    # Carregar dados
    items_df, transactions_df, people_df, projects_df = carregar_dados()

    # Filtrar visualização pelo setor
    if setor != "Todos":
        items_df = items_df[items_df["sector"] == setor]
        item_ids = set(items_df["id"])
        transactions_df = transactions_df[transactions_df["item"].isin(item_ids)]

    # Move item selection here, before the first table
    item_options = {row["name"]: row["id"] for _, row in items_df.iterrows()}
    
    # Reset selected item if it's not in the current sector's items
    if 'selected_item' in st.session_state and st.session_state.selected_item not in item_options:
        st.session_state.selected_item = list(item_options.keys())[0] if item_options else None
    
    if item_options:
        selected_item = st.selectbox(
            "Item",
            list(item_options.keys()),
            key="item_selector",
            index=list(item_options.keys()).index(st.session_state.selected_item) if 'selected_item' in st.session_state else 0
        )
        # Get current amount for selected item
        saldo_df = calcular_saldo(items_df, transactions_df)
        current_amount = saldo_df[saldo_df['name'] == selected_item]['Saldo Atual'].iloc[0]
        st.markdown(f"Quantidade em estoque atualmente: **{current_amount}**")

        # Use the selected item from the single selector
        selected_item_id = item_options[selected_item]
        
        dados_grafico = preparar_dados_grafico(items_df, transactions_df, selected_item_id)
        
        # Filter data for the specific selected item
        if selected_item and not dados_grafico.empty:
            dados_grafico = dados_grafico[[selected_item]]
        
        if not dados_grafico.empty:
            # Reset index to make date a column
            dados_grafico = dados_grafico.reset_index()
            
            # Format dates for display
            dados_grafico['date'] = pd.to_datetime(dados_grafico['date']).dt.strftime('%d/%m/%Y')
            
            # Get today's date in the same format
            hoje = datetime.now(pytz.timezone('America/Sao_Paulo')).strftime('%d/%m/%Y')
            
            # Replace last date with "Hoje" only if it matches today's date
            dates = dados_grafico['date'].tolist()
            if dates and dates[-1] == hoje:
                dates[-1] = "Hoje"
            
            # Prepare data for candlestick
            values = dados_grafico[dados_grafico.columns[1]].values.astype(float).tolist()
            candlestick_data = []
            for i in range(len(values)):
                if i == 0:
                    # For first point: [open, close, min, max]
                    candlestick_data.append([0, values[i], 0, values[i]])
                else:
                    # For other points: [previous close, current close, min(prev,current), max(prev,current)]
                    candlestick_data.append([
                        values[i-1],
                        values[i],
                        min(values[i-1], values[i]),
                        max(values[i-1], values[i])
                    ])
            
            try:
                # Convert data for Plotly
                opens = [float(data[0]) for data in candlestick_data]
                closes = [float(data[1]) for data in candlestick_data]
                lows = [float(data[2]) for data in candlestick_data]
                highs = [float(data[3]) for data in candlestick_data]
                
                # Create hover text
                hover_texts = [
                    f"Data: {date}<br>" +
                    f"Início do dia: {open_val:.0f}<br>" +
                    f"Final do dia: {close_val:.0f}"
                    for date, open_val, close_val, low_val, high_val 
                    in zip(dates, opens, closes, lows, highs)
                ]
                
                # Create Plotly candlestick chart
                fig = go.Figure()
                fig.add_trace(go.Candlestick(
                    x=dates,
                    open=opens,
                    high=highs,
                    low=lows,
                    close=closes,
                    name='Quantidade',
                    increasing=dict(line=dict(color='#91cc75')),  # green for increase
                    decreasing=dict(line=dict(color='#ee6666')),  # red for decrease
                    text=hover_texts,
                    hoverinfo='text'
                ))
                
                # Update layout
                fig.update_layout(
                    plot_bgcolor='white',
                    xaxis=dict(
                        showgrid=True,
                        gridwidth=1,
                        gridcolor='rgba(128,128,128,0.2)',
                        showline=True,
                        linewidth=1,
                        linecolor='rgba(128,128,128,0.2)',
                        rangeslider=dict(visible=False)  # Remove the range slider
                    ),
                    yaxis=dict(
                        title='Quantidade',
                        showgrid=True,
                        gridwidth=1,
                        gridcolor='rgba(128,128,128,0.2)',
                        showline=True,
                        linewidth=1,
                        linecolor='rgba(128,128,128,0.2)'
                    ),
                    margin=dict(l=40, r=40, t=40, b=40)
                )
                
                # Display the plot
                st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.error(f"Erro ao criar o gráfico: {str(e)}")
                st.write("Dados do gráfico:", candlestick_data)
            
            # Add transaction history table
            st.subheader(f"Histórico de {selected_item.lower()}")
            
            # Get transactions for the selected item
            item_transactions = transactions_df[transactions_df['item'] == selected_item_id].copy()
            if not item_transactions.empty:
                # Convert timestamp to datetime and format
                item_transactions['timestamp'] = pd.to_datetime(item_transactions['timestamp'])
                item_transactions = item_transactions.sort_values('timestamp', ascending=False)
                item_transactions['timestamp'] = item_transactions['timestamp'].dt.strftime("%d/%m/%Y %H:%M:%S")
                
                # Join with people data to get author names
                if not people_df.empty and 'author' in item_transactions.columns:
                    item_transactions = pd.merge(
                        item_transactions,
                        people_df[['id', 'name']],
                        left_on='author',
                        right_on='id',
                        how='left',
                        suffixes=('', '_author')
                    )

                # Format the table columns
                rename_cols = {
                    'timestamp': 'Data/Hora',
                    'amount': 'Qtd',
                    'transaction_type': 'Tipo',
                    'observation': 'Observação'
                }
                
                # Add author column if available
                if 'name' in item_transactions.columns:
                    rename_cols['name'] = 'Autor'
                elif 'name_author' in item_transactions.columns:
                    rename_cols['name_author'] = 'Autor'
                
                item_transactions = item_transactions.rename(columns=rename_cols)
                
                # Style the table
                st.markdown("""
                    <style>
                    .dataframe {
                        font-size: 1rem;
                        width: 100%;
                    }
                    .dataframe td, .dataframe th {
                        white-space: nowrap;
                        text-align: center !important;
                    }
                    .dataframe th {
                        background-color: rgba(128, 128, 128, 0.1);
                    }
                    </style>
                """, unsafe_allow_html=True)
                
                # Get the columns we want to display
                display_cols = ['Data/Hora', 'Qtd', 'Tipo']
                if 'Autor' in item_transactions.columns:
                    display_cols.append('Autor')
                display_cols.append('Observação')

                # Display the table
                st.dataframe(
                    item_transactions[display_cols],
                    hide_index=True,
                    use_container_width=True
                )
            else:
                st.info("Nenhuma movimentação encontrada para este item.")
            
            st.session_state.selected_item = selected_item

    # 2. List of items
    st.subheader(f"Estoque atual de todos os itens de {setor.lower()}")
    mostrar_estoque(items_df, transactions_df)

    # 4. Register transaction
    st.subheader("Registrar nova movimentação")
    if item_options:
        # Radio button outside the form to control form state
        movimento_tipo = st.radio(
            "Tipo de Movimentação",
            ["Entrada", "Saída", "Contagem inicial"]
        )

        # Project selection is now OUTSIDE the form to allow for immediate refresh
        project_options = {row["name"]: row["id"] for _, row in projects_df.iterrows()}
        project_list = ["Nenhum"] + list(project_options.keys())
        selected_project = st.selectbox(
            "Projeto",
            options=project_list,
            key=f"project_select_{movimento_tipo}" # Keep key dynamic to reset on type change
        )
        
        with st.form(f"nova_movimentacao_{movimento_tipo}"):
            col1, col2 = st.columns([1.5, 3])
            
            with col1:
                quantidade = st.number_input("Quantidade", min_value=1, step=1)
            
            with col2:
                # Author selection
                author_options = {row["name"]: row["id"] for _, row in people_df.iterrows()}
                selected_author = st.selectbox(
                    "Autor",
                    options=list(author_options.keys()),
                    key=f"author_select_{movimento_tipo}"
                )

            # Determine observation value and disabled state
            obs_value = ""
            obs_disabled = False
            if movimento_tipo == "Contagem inicial":
                obs_value = "Contagem inicial"
                obs_disabled = True
            elif selected_project != "Nenhum":
                obs_value = selected_project
                obs_disabled = True

            observacao = st.text_input(
                "Observação (opcional)",
                value=obs_value,
                disabled=obs_disabled,
                key=f"obs_input_{movimento_tipo}_{selected_project}"  # Dynamic key still useful
            )
            
            submitted = st.form_submit_button("Registrar", use_container_width=True)
            if submitted:
                tipo = "Entrada" if movimento_tipo == "Contagem inicial" else movimento_tipo
                obs = observacao
                
                criar_movimentacao(
                    item_options[selected_item],
                    quantidade,
                    tipo,
                    obs,
                    author_options[selected_author]
                )
                st.toast("Movimentação registrada com sucesso!", icon="✅")
                # Reload transaction history
                st.rerun()

    # 6. Export daily report
    # Carregar dados novamente sem filtro para o relatório
    items_df_full, transactions_df_full, _, _ = carregar_dados()
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
        if not transacoes_hoje.empty:
            transacoes_hoje["Data/Hora"] = transacoes_hoje["Data/Hora"].dt.strftime("%d/%m/%Y %H:%M:%S")

    pdf_buffer = gerar_pdf(transacoes_hoje, relatorio)
    now_str = datetime.now().strftime("%Y-%m-%d_%H-%M")
    st.download_button(
        label="Exportar estoque atual + transações do dia",
        data=pdf_buffer,
        file_name=f"relatorio_estoque_{now_str}.pdf",
        mime="application/pdf",
        use_container_width=True
    )

if __name__ == "__main__":
    main() 
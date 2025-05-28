import pandas as pd
import streamlit as st
from datetime import datetime

def carregar_dados(tipo):
    base = tipo.lower()
    estoque = pd.read_csv(f"data/{base}.csv")
    try:
        historico = pd.read_csv(f"data/{base}_historico.csv")
    except FileNotFoundError:
        historico = pd.DataFrame(columns=["Data", "Tipo", "Descricao", "Quantidade", "Observação"])
    return estoque, historico

def salvar_dados(tipo, estoque, historico):
    base = tipo.lower()
    estoque.to_csv(f"data/{base}.csv", index=False)
    historico.to_csv(f"data/{base}_historico.csv", index=False)

def mostrar_estoque(df):
    st.subheader("📋 Estoque Atual")
    if 'Descricao' in df.columns:
        df = df.drop(columns=['Descricao'])
    st.dataframe(df)

def mostrar_movimentacoes(historico):
    st.subheader("📈 Histórico de Movimentações")
    st.dataframe(historico.sort_values("Data", ascending=False))

def salvar_movimentacao(tipo, estoque, historico):
    if {"Linha", "Item", "Gramatura"}.issubset(estoque.columns):
        estoque["Descricao"] = estoque[["Linha", "Item", "Gramatura"]].fillna("").agg(" ".join, axis=1).str.strip()
    else:
        estoque["Descricao"] = estoque["Item"]

    descricao = st.selectbox("Item:", estoque["Descricao"].unique())
    tipo_mov = st.radio("Tipo:", ["Entrada", "Saída"])
    quantidade = st.number_input("Quantidade:", min_value=1, step=1)
    observacao = st.text_input("Observação (opcional):")

    if st.button("Registrar"):
        idx = estoque[estoque["Descricao"] == descricao].index
        if len(idx) == 0:
            st.error("Item não encontrado.")
            return
        idx = idx[0]

        if tipo_mov == "Entrada":
            estoque.loc[idx, "Quantidade"] += quantidade
        else:
            if estoque.loc[idx, "Quantidade"] < quantidade:
                st.error("Quantidade insuficiente no estoque.")
                return
            estoque.loc[idx, "Quantidade"] -= quantidade

        nova_linha = pd.DataFrame([{
            "Data": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Tipo": tipo_mov,
            "Descricao": descricao,
            "Quantidade": quantidade,
            "Observação": observacao
        }])

        historico = pd.concat([historico, nova_linha], ignore_index=True)

        salvar_dados(tipo, estoque, historico)
        st.success("Movimentação registrada com sucesso.")
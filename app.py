import streamlit as st
from utils import carregar_dados, salvar_movimentacao, mostrar_estoque, mostrar_movimentacoes

st.set_page_config(page_title="Controle de Estoque - Touché", layout="wide")

st.title("📦 Controle de Estoque - Touché")

aba = st.sidebar.radio("Selecionar operação:", ["Consultar Estoque", "Registrar Movimentação", "Consultar Movimentações"])

tipo_estoque = st.sidebar.selectbox("Tipo de Estoque:", ["Papeis", "Materiais"])

dados_estoque, historico = carregar_dados(tipo_estoque)

if aba == "Consultar Estoque":
    mostrar_estoque(dados_estoque)

elif aba == "Registrar Movimentação":
    salvar_movimentacao(tipo_estoque, dados_estoque, historico)

elif aba == "Consultar Movimentações":
    mostrar_movimentacoes(historico)
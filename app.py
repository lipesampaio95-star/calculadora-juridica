import streamlit as st
import pandas as pd
from fpdf import FPDF
import io
from datetime import datetime

# --- 1. CONFIGURAÇÃO INICIAL ---
st.set_page_config(
    page_title="Precificação Jurídica | Delgado & Sampaio",
    page_icon="⚖️",
    layout="wide"
)

st.title("⚖️ Delgado & Sampaio Sociedade de Advogados ⚖️")
st.markdown("---")

# --- 2. FUNÇÕES DE EXPORTAÇÃO ---
def gerar_pdf(cliente, servico, horas, valor_total, valor_hora, margem, impostos, custos_totais):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, f"PROPOSTA DE HONORARIOS", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, f"Cliente: {cliente}", ln=True)
    pdf.set_font("Arial", size=12)
    pdf.cell(0, 10, f"Servico: {servico}", ln=True)
    pdf.cell(0, 10, f"Data: {datetime.now().strftime('%d/%m/%Y')}", ln=True)
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "Escopo e Investimento:", ln=True)
    pdf.set_font("Arial", size=12)
    pdf.cell(0, 10, f"Horas Estimadas: {horas}h", ln=True)
    pdf.cell(0, 10, f"Valor Base da Hora Tecnica: R$ {valor_hora:,.2f}", ln=True)
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, f"VALOR TOTAL DOS HONORARIOS: R$ {valor_total:,.2f}", ln=True)
    pdf.ln(20)
    pdf.set_font("Arial", 'I', 8)
    pdf.cell(0, 10, f"Nota Interna: Margem Liq. {margem*100:.0f}% | Impostos {impostos*100:.0f}%", ln=True)
    return pdf.output(dest='S').encode('latin-1', 'replace')

def gerar_excel(dados_dict):
    output = io.BytesIO()
    writer = pd.ExcelWriter(output, engine='openpyxl')
    df = pd.DataFrame([dados_dict])
    df.to_excel(writer, index=False, sheet_name='Precificacao')
    writer.close()
    return output.getvalue()

# --- 3. BARRA LATERAL: CUSTOS ---
st.sidebar.header("🏢 Custos Operacionais")

# MODO DE ENTRADA
modo_entrada = st.sidebar.radio(
    "Fonte dos Dados:",
    ("Custos Fixos 2025 (Salvo)", "Upload Relatório/Planilha")
)

custo_fixo_total = 0.0

# --- A: DADOS SALVOS ---
if modo_entrada == "Custos Fixos 2025 (Salvo)":
    st.sidebar.caption("Dados baseados na planilha 'Custo Operacional Atualizado'")
    with st.sidebar.expander("📝 Ajustar Valores Padrão", expanded=True):
        aluguel = st.number_input("Condomínio/Aluguel", value=2071.76, step=50.0)
        software = st.number_input("Softwares/Sistemas", value=3602.94, step=100.0)
        administrativo = st.number_input("Contador/BPO", value=1325.54, step=50.0)
        
        st.markdown("**Equipe e Sócios**")
        equipe_fixa = st.number_input("Salários Equipe (CLT+Encargos)", value=11281.60, step=100.0)
        pro_labore = st.number_input("Pró-Labore (Sócios)", value=20000.00, step=500.0)
        
        st.markdown("**Outros**")
        outros_fixos = st.number_input("Gerais (Energia, Saúde, Manut.)", value=7836.89, step=100.0)
        
        custo_fixo_total = aluguel + software + administrativo + equipe_fixa + pro_labore + outros_fixos

# --- B: UPLOAD COM FILTRO ANTI-DUPLICAÇÃO ---
else:
    st.sidebar.info("O sistema ignora linhas de 'Total' para não duplicar.")
    arquivo_upload = st.sidebar.file_uploader("Subir arquivo Excel/CSV", type=['xlsx', 'xls', 'csv'])
    
    if arquivo_upload is not None:
        try:
            if arquivo_upload.name.endswith('.csv'):
                df_custos = pd.read_csv(arquivo_upload)
            else:
                df_custos = pd.read_excel(arquivo_upload)
            
            df_custos.columns = df_custos.columns.str.strip()
            
            # 1. Identifica colunas de Texto (Descrição) e Valor
            col_valor = None
            col_desc = None
            
            for col in df_custos.columns:
                col_lower = col.lower()
                # Acha coluna de valor
                if any(x in col_lower for x in ['valor', 'custo', 'amount', 'total', 'r$']):
                    try:
                        pd.to_numeric(df_custos[col], errors='coerce')
                        col_valor = col
                    except: pass
                # Acha coluna de descrição
                if any(x in col_lower for x in ['desc', 'historico', 'nome', 'item']):
                    col_desc = col

            if col_valor:
                # 2. FILTRO INTELIGENTE: Remove linha de TOTAL
                if col_desc:
                    # Remove linhas onde a descrição contém "total" (maiúsculo ou minúsculo)
                    df_filtrado = df_custos[~df_custos[col_desc].astype(str).str.contains('total', case=False, na=False)]
                else:
                    df_filtrado = df_custos

                # 3. Verifica se é Despesa (Negativo) ou Lista de Custos (Positivo)
                soma_negativos = df_filtrado[df_filtrado[col_valor] < 0][col_valor].sum()
                
                if soma_negativos < 0:
                    custo_fixo_total = abs(soma_negativos)
                    st.sidebar.success(f"✅ Despesas (Negativas): R$ {custo_fixo_total:,.2f}")
                else:
                    custo_fixo_total = df_filtrado[col_valor].sum()
                    st.sidebar.success(f"✅ Soma da Lista: R$ {custo_fixo_total:,.2f}")
                    if col_desc:
                        st.sidebar.caption("Linhas contendo 'Total' foram ignoradas.")
                
                with st.sidebar.expander("Verificar Dados Lidos"):
                    st.dataframe(df_filtrado[[col_desc, col_valor]] if col_desc else df_filtrado, hide_index=True)

            else:
                st.sidebar.error("❌ Não encontrei coluna de valor.")
        except Exception as e:
            st.sidebar.error(f"Erro: {e}")

# Exibe Total
if modo_entrada == "Custos Fixos 2025 (Salvo)":
    st.sidebar.markdown(f"**Custo Mensal Total: R$ {custo_fixo_total:,.2f}**")

st.sidebar.markdown("---")

# --- MÃO DE OBRA ---
with st.sidebar.expander("2. Capacidade Produtiva", expanded=True):
    horas_disponiveis = st.number_input("Horas Totais Escritório (Mês)", value=320)
    eficiencia = st.slider("Eficiência Produtiva (%)", 50, 100, 75)
    salario_extra = st.number_input("Custo Mão de Obra Extra (R$)", value=0.00)

# CÁLCULOS
horas_faturaveis = horas_disponiveis * (eficiencia / 100)
rateio_hora_fixa = custo_fixo_total / horas_faturaveis if horas_faturaveis > 0 else 0
custo_hora_tecnica = salario_extra / horas_faturaveis if horas_faturaveis > 0 else 0
custo_hora_total_base = rateio_hora_fixa + custo_hora_tecnica

st.sidebar.info(f"💰 **Custo Hora (Break-even):**\nR$ {custo_hora_total_base:,.2f}")

# --- PRINCIPAL ---
col1, col2 = st.columns(2)
with col1:
    st.subheader("📁 Novo Caso")
    cliente = st.text_input("Cliente")
    servico = st.text_input("Serviço")
    c1, c2 = st.columns(2)
    horas = c1.number_input("Horas Estimadas", 1, 1000, 10)
    custos_var = c2.number_input("Custos Extras (R$)", 0.00)
    st.subheader("🎯 Margens")
    m1, m2 = st.columns(2)
    margem = m1.number_input("Margem Lucro (%)", value=40.0) / 100
    imposto = m2.number_input("Imposto (%)", value=10.0) / 100

custo_op = (custo_hora_total_base * horas) + custos_var
divisor = 1 - (margem + imposto)
if divisor <= 0:
    preco = 0
    st.error("Erro: Margem excessiva.")
else:
    preco = custo_op / divisor

with col2:
    st.subheader("📊 Resultado")
    st.metric("Preço Sugerido", f"R$ {preco:,.2f}")
    st.metric("Preço/Hora", f"R$ {(preco/horas):,.2f}")
    st.bar_chart(pd.DataFrame({'Tipo': ['Custo', 'Imposto', 'Lucro'], 'Valor': [custo_op, preco*imposto, preco*margem]}).set_index('Tipo'))

st.markdown("---")
if preco > 0:
    c_pdf, c_xls = st.columns(2)
    with c_pdf:
        st.download_button("📄 PDF Proposta", gerar_pdf(cliente, servico, horas, preco, preco/horas, margem, imposto, custo_op), "proposta.pdf", "application/pdf")
    with c_xls:
        st.download_button("📊 Excel Memória", gerar_excel({"Cliente": cliente, "Preço": preco}), "calculo.xlsx")

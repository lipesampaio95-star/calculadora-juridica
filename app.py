import streamlit as st
import pandas as pd
from fpdf import FPDF
import io
from datetime import datetime

# --- 1. CONFIGURAÇÃO INICIAL DA PÁGINA ---
st.set_page_config(
    page_title="Precificação Jurídica | Escritório",
    page_icon="⚖️",
    layout="wide"
)

st.title("⚖️ Sistema de Precificação de Honorários")
st.markdown("---")

# --- 2. FUNÇÕES DE EXPORTAÇÃO (PDF E EXCEL) ---

def gerar_pdf(cliente, servico, horas, valor_total, valor_hora, margem, impostos, custos_totais):
    """Gera o PDF da Proposta Formal"""
    pdf = FPDF()
    pdf.add_page()
    
    # Cabeçalho
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, f"PROPOSTA DE HONORARIOS", ln=True, align='C')
    pdf.ln(10)
    
    # Dados do Cliente
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, f"Cliente: {cliente}", ln=True)
    pdf.set_font("Arial", size=12)
    pdf.cell(0, 10, f"Servico: {servico}", ln=True)
    pdf.cell(0, 10, f"Data: {datetime.now().strftime('%d/%m/%Y')}", ln=True)
    pdf.ln(10)
    
    # Detalhamento
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "Escopo e Investimento:", ln=True)
    pdf.set_font("Arial", size=12)
    pdf.cell(0, 10, f"Horas Estimadas: {horas}h", ln=True)
    pdf.cell(0, 10, f"Valor Base da Hora Tecnica: R$ {valor_hora:,.2f}", ln=True)
    pdf.ln(10)
    
    # Valor Final
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, f"VALOR TOTAL DOS HONORARIOS: R$ {valor_total:,.2f}", ln=True)
    
    # Rodapé Técnico (Opcional - útil para conferência interna)
    pdf.ln(20)
    pdf.set_font("Arial", 'I', 8)
    pdf.cell(0, 10, f"Nota Interna: Margem Liq. {margem*100:.0f}% | Impostos {impostos*100:.0f}%", ln=True)
    
    # Retorna o binário codificado em Latin-1 para aceitar acentos básicos
    return pdf.output(dest='S').encode('latin-1', 'replace')

def gerar_excel(dados_dict):
    """Gera o arquivo Excel para download"""
    output = io.BytesIO()
    writer = pd.ExcelWriter(output, engine='openpyxl')
    df = pd.DataFrame([dados_dict])
    df.to_excel(writer, index=False, sheet_name='Precificacao')
    writer.close()
    return output.getvalue()

# --- 3. BARRA LATERAL: ENTRADA DE DADOS ---

st.sidebar.header("🏢 Custos do Escritório")

# SELEÇÃO: MODO DE ENTRADA DOS CUSTOS FIXOS
modo_entrada = st.sidebar.radio(
    "Como deseja inserir os Custos Fixos?",
    ("Digitar Manualmente", "Upload de Planilha (.xlsx)")
)

custo_fixo_total = 0.0

# Lógica A: Entrada Manual
if modo_entrada == "Digitar Manualmente":
    with st.sidebar.expander("📝 Preenchimento Manual", expanded=True):
        aluguel = st.number_input("Aluguel + Condomínio (R$)", value=2500.00, step=50.0)
        software = st.number_input("Software / Sistemas (R$)", value=300.00, step=10.0)
        marketing = st.number_input("Marketing / Site (R$)", value=500.00, step=50.0)
        administrativo = st.number_input("Equipe Adm. + Contador (R$)", value=2000.00, step=50.0)
        outros_fixos = st.number_input("Outros / Diversos (R$)", value=500.00, step=50.0)
        
        custo_fixo_total = aluguel + software + marketing + administrativo + outros_fixos

# Lógica B: Upload de Arquivo
else:
    st.sidebar.info("A planilha deve ter uma coluna chamada **'Valor'**, **'Custo'** ou **'Total'**.")
    arquivo_upload = st.sidebar.file_uploader("Subir arquivo Excel", type=['xlsx', 'xls'])
    
    if arquivo_upload is not None:
        try:
            df_custos = pd.read_excel(arquivo_upload)
            
            # Algoritmo para encontrar a coluna de valor automaticamente
            colunas_possiveis = ['Valor', 'valor', 'Custo', 'custo', 'Total', 'total', 'Amount']
            coluna_alvo = next((col for col in colunas_possiveis if col in df_custos.columns), None)
            
            if coluna_alvo:
                custo_fixo_total = df_custos[coluna_alvo].sum()
                st.sidebar.success(f"✅ Arquivo lido com sucesso!")
                st.sidebar.metric("Custo Fixo Importado", f"R$ {custo_fixo_total:,.2f}")
                
                with st.sidebar.expander("Ver Itens Importados"):
                    st.dataframe(df_custos, hide_index=True)
            else:
                st.sidebar.error("❌ Não encontrei coluna de valor (ex: 'Valor', 'Custo').")
        except Exception as e:
            st.sidebar.error(f"Erro ao ler arquivo: {e}")
    else:
        st.sidebar.warning("Aguardando upload...")

# Exibe o total calculado (seja manual ou upload)
if modo_entrada == "Digitar Manualmente":
    st.sidebar.markdown(f"**Total Fixos: R$ {custo_fixo_total:,.2f}**")

st.sidebar.markdown("---")

# MÃO DE OBRA
with st.sidebar.expander("2. Capacidade e Equipe Jurídica", expanded=True):
    horas_disponiveis = st.number_input("Horas Totais Disponíveis (Mês)", value=160, help="Soma das horas de todos os advogados")
    eficiencia = st.slider("Eficiência Produtiva (%)", 50, 100, 80, help="% do tempo faturável")
    salario_adv = st.number_input("Custo Mensal Advogados (R$)", value=8000.00, help="Salário + Encargos")

# CÁLCULOS INTERNOS DE CUSTO HORA
horas_faturaveis = horas_disponiveis * (eficiencia / 100)
rateio_hora_fixa = custo_fixo_total / horas_faturaveis if horas_faturaveis > 0 else 0
custo_hora_tecnica = salario_adv / horas_faturaveis if horas_faturaveis > 0 else 0
custo_hora_total_base = rateio_hora_fixa + custo_hora_tecnica

st.sidebar.info(f"💰 **Custo Hora (Break-even):**\nR$ {custo_hora_total_base:,.2f}")


# --- 4. ÁREA PRINCIPAL: DADOS DO CASO ---
col_entrada, col_saida = st.columns([1, 1])

with col_entrada:
    st.subheader("📁 Dados do Novo Caso")
    nome_cliente = st.text_input("Nome do Cliente", placeholder="Ex: Cliente Exemplo Ltda")
    tipo_servico = st.text_input("Tipo de Serviço", placeholder="Ex: Ação Trabalhista")
    
    c1, c2 = st.columns(2)
    horas_estimadas = c1.number_input("Horas Estimadas", min_value=1, value=10)
    custos_variaveis = c2.number_input("Custos Variáveis (R$)", value=0.00, help="Deslocamento, custas, etc.")

    st.markdown("### 🎯 Definição de Margem")
    m1, m2 = st.columns(2)
    margem_lucro_pct = m1.number_input("Margem de Lucro (%)", value=40.0, step=1.0)
    impostos_pct = m2.number_input("Impostos (NF) (%)", value=10.0, step=0.5)

# --- 5. MOTOR DE CÁLCULO FINANCEIRO ---
margem_decimal = margem_lucro_pct / 100
impostos_decimal = impostos_pct / 100

# Custo Operacional do Serviço
custo_operacional_servico = (custo_hora_total_base * horas_estimadas) + custos_variaveis

# FÓRMULA DE MARKUP DIVISOR
# Preço = Custo / (1 - (Margem + Impostos))
divisor_markup = 1 - (margem_decimal + impostos_decimal)

if divisor_markup <= 0:
    preco_final = 0
    erro_calculo = True
else:
    preco_final = custo_operacional_servico / divisor_markup
    erro_calculo = False

# Decomposição dos valores
valor_impostos = preco_final * impostos_decimal
valor_lucro = preco_final * margem_decimal

# --- 6. EXIBIÇÃO DE RESULTADOS ---
with col_saida:
    st.subheader("📊 Resultado Financeiro")
    
    if erro_calculo:
        st.error("⚠️ Erro Matemático: A soma da Margem de Lucro e Impostos ultrapassa 100%. Reduza as porcentagens.")
    else:
        # Métricas Principais
        col_met1, col_met2 = st.columns(2)
        col_met1.metric("Preço Sugerido (Total)", f"R$ {preco_final:,.2f}")
        col_met2.metric("Valor da Hora Cobrada", f"R$ {(preco_final/horas_estimadas):,.2f}")
        
        st.markdown("---")
        
        # Gráfico
        st.markdown("**Composição do Preço:**")
        df_chart = pd.DataFrame({
            'Componente': ['Custos (Fixo+Var)', 'Impostos (NF)', 'Lucro Líquido'],
            'Valor': [custo_operacional_servico, valor_impostos, valor_lucro]
        })
        st.bar_chart(df_chart.set_index('Componente'), color=["#FF4B4B"])
        
        # Detalhes Numéricos
        with st.expander("Ver Detalhes (Matemática)"):
            st.write(f"**(+) Custo Operacional:** R$ {custo_operacional_servico:,.2f}")
            st.write(f"**(+) Impostos:** R$ {valor_impostos:,.2f}")
            st.write(f"**(+) Lucro Líquido:** R$ {valor_lucro:,.2f}")
            st.markdown(f"**(=) Preço Final:** R$ {preco_final:,.2f}")

# --- 7. ÁREA DE EXPORTAÇÃO (DOWNLOADS) ---
st.markdown("---")
st.subheader("📥 Exportar Documentos")

if not erro_calculo:
    col_pdf, col_xls = st.columns(2)
    
    # Botão PDF
    with col_pdf:
        pdf_bytes = gerar_pdf(
            nome_cliente, tipo_servico, horas_estimadas, 
            preco_final, preco_final/horas_estimadas, 
            margem_decimal, impostos_decimal, custo_operacional_servico
        )
        st.download_button(
            label="📄 Baixar Proposta (PDF)",
            data=pdf_bytes,
            file_name=f"Proposta_{nome_cliente.replace(' ', '_')}.pdf",
            mime="application/pdf"
        )
        
    # Botão Excel
    with col_xls:
        dados_excel = {
            "Data": datetime.now().strftime('%d/%m/%Y'),
            "Cliente": nome_cliente,
            "Serviço": tipo_servico,
            "Horas Estimadas": horas_estimadas,
            "Custo Total Operacional": custo_operacional_servico,
            "Margem Lucro %": margem_lucro_pct,
            "Impostos %": impostos_pct,
            "Preço Final": preco_final,
            "Lucro Líquido R$": valor_lucro
        }
        excel_bytes = gerar_excel(dados_excel)
        st.download_button(
            label="📊 Baixar Memória de Cálculo (.xlsx)",
            data=excel_bytes,
            file_name=f"Calculo_{nome_cliente.replace(' ', '_')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

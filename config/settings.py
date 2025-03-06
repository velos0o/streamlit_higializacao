"""Configurações globais para o dashboard de Higienização"""
import streamlit as st
from pathlib import Path

# Caminho base do projeto
BASE_PATH = Path(__file__).parent.parent

# Configuração da categoria do Bitrix a ser usada
# ATENÇÃO: Este valor DEVE ser alterado para o ID da categoria correta no seu Bitrix24
CATEGORY_ID = 32  # Altere para a categoria correta 

# Flag para indicar se a configuração está completa
CONFIG_VERIFICADA = True

# Campos personalizados para análise
CAMPOS_PERSONALIZADOS = {
    "REQUERIMENTO": "UF_CRM_1741183828129",
    "DOCUMENTACAO": "UF_CRM_1741183785848",
    "CADASTRO_ARVORE": "UF_CRM_1741183721969",
    "ESTRUTURA_ARVORE": "UF_CRM_1741183685327",
    "EMISSOES_BRASILEIRAS": "UF_CRM_1741198696",
    "STATUS_HIGILIZACAO": "UF_CRM_HIGILIZACAO_STATUS"
}

# Cores para o tema do dashboard
CORES = {
    "azul_principal": "#0063B2",
    "azul_claro": "#9DC3E6",
    "cinza_claro": "#F8F9FA",
    "cinza_medio": "#DEE2E6",
    "cinza_escuro": "#6C757D",
    "branco": "#FFFFFF",
    "pendencia": "#FFC107",
    "completo": "#28A745",
    "incompleto": "#FD7E14",
    "fundo": "#F5F7FA",
    "destaque": "#007BFF"
}

def configurar_pagina():
    """Configuração da página do Streamlit"""
    st.set_page_config(
        page_title="Dashboard de Higienização",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Aplicar estilo CSS
    aplicar_estilo_config()

def aplicar_estilo_config():
    """Aplica estilo CSS global à aplicação"""
    estilo = f"""
        <style>
            /* Configurações gerais */
            .main {{
                background-color: {CORES['fundo']};
                padding: 0.5rem;
            }}
            
            .stApp {{
                max-width: 100%;
                margin: 0 auto;
            }}
            
            /* Remover margens extras e paddings */
            .block-container {{
                padding-top: 1rem;
                padding-bottom: 1rem;
                padding-left: 1.5rem;
                padding-right: 1.5rem;
            }}
            
            /* Proporção 16:9 para gráficos e containers */
            [data-testid="stVerticalBlock"] {{
                gap: 0.5rem;
            }}
            
            /* Ajustes para visualização em tela cheia */
            #MainMenu {{visibility: hidden;}}
            footer {{visibility: hidden;}}
            header {{visibility: hidden;}}
            
            /* Minimizar espaços entre elementos */
            div.element-container {{
                margin-bottom: 0.5rem;
            }}
            
            /* Otimizar para formato widescreen 16:9 */
            @media screen and (min-aspect-ratio: 16/9) {{
                .main {{
                    padding: 0.25rem;
                }}
                
                .block-container {{
                    padding-top: 0.5rem;
                    padding-bottom: 0.5rem;
                }}
            }}
            
            /* Cabeçalho */
            .cabecalho {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 1rem;
                background-color: {CORES['branco']};
                border-radius: 10px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.05);
                margin-bottom: 20px;
            }}
            
            /* Cards */
            .card {{
                background-color: {CORES['branco']};
                border-radius: 8px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.05);
                padding: 20px;
                margin-bottom: 20px;
            }}
            
            .card-titulo {{
                color: {CORES['azul_principal']};
                font-size: 18px;
                font-weight: 600;
                margin-bottom: 15px;
                border-bottom: 1px solid {CORES['cinza_medio']};
                padding-bottom: 8px;
            }}
            
            /* Tabelas */
            .dataframe {{
                width: 100%;
                border-collapse: collapse;
            }}
            
            .dataframe th {{
                background-color: {CORES['azul_principal']};
                color: {CORES['branco']};
                padding: 8px 15px;
                text-align: left;
                font-weight: 500;
            }}
            
            .dataframe tr:nth-child(even) {{
                background-color: {CORES['cinza_claro']};
            }}
            
            .dataframe tr:hover {{
                background-color: {CORES['cinza_medio']};
            }}
            
            .dataframe td {{
                padding: 8px 15px;
                border-bottom: 1px solid {CORES['cinza_medio']};
            }}
            
            /* Status */
            .status-pendencia {{
                background-color: {CORES['pendencia']};
                color: {CORES['branco']};
                padding: 3px 8px;
                border-radius: 4px;
                font-size: 12px;
                font-weight: 500;
            }}
            
            .status-completo {{
                background-color: {CORES['completo']};
                color: {CORES['branco']};
                padding: 3px 8px;
                border-radius: 4px;
                font-size: 12px;
                font-weight: 500;
            }}
            
            .status-incompleto {{
                background-color: {CORES['incompleto']};
                color: {CORES['branco']};
                padding: 3px 8px;
                border-radius: 4px;
                font-size: 12px;
                font-weight: 500;
            }}
        </style>
    """
    
    st.markdown(estilo, unsafe_allow_html=True) 
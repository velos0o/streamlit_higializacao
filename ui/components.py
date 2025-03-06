"""Componentes de interface para o dashboard"""
import streamlit as st
import pandas as pd
from config.settings import CORES
from pathlib import Path
import base64
from contextlib import contextmanager

@st.cache_data
def carregar_imagem_base64(caminho: str) -> str:
    """
    Carrega uma imagem e converte para base64
    
    Args:
        caminho: Caminho do arquivo de imagem
        
    Returns:
        String em base64 da imagem
    """
    try:
        with open(caminho, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    except Exception as e:
        st.error(f"Erro ao carregar imagem: {e}")
        return ""

def cabecalho():
    """Renderiza o cabeçalho do relatório"""
    try:
        logo_path = Path(__file__).parent.parent / "logo.svg.svg"
        logo_base64 = carregar_imagem_base64(str(logo_path))
        
        # Cabeçalho com logo e título
        html = f"""
        <div class="cabecalho">
            <div style="display: flex; align-items: center;">
                <img src="data:image/svg+xml;base64,{logo_base64}" style="height: 50px; margin-right: 15px;">
                <div>
                    <h1 style="margin: 0; color: {CORES['azul_principal']}; font-size: 22px;">Relatório de Higienização</h1>
                    <p style="margin: 0; color: {CORES['cinza_escuro']}; font-size: 13px;">Monitoramento de status e pendências</p>
                </div>
            </div>
            <div>
                <p style="margin: 0; color: {CORES['cinza_escuro']}; font-size: 12px;">Atualizado em: {pd.Timestamp.now().strftime('%d/%m/%Y %H:%M')}</p>
            </div>
        </div>
        """
        
        st.markdown(html, unsafe_allow_html=True)
    except Exception as e:
        # Fallback simples se não conseguir carregar a logo
        st.title("Dashboard de Higienização")
        st.caption("Monitoramento de status e pendências")
        st.error(f"Erro ao carregar cabeçalho: {e}")

def cartao_metrica(titulo: str, valor: str, icone: str = None, cor: str = CORES["azul_principal"],
                 delta: str = None, help_text: str = None):
    """
    Renderiza um cartão com métrica estilizado
    
    Args:
        titulo: Título da métrica
        valor: Valor da métrica
        icone: Emoji ou ícone para a métrica
        cor: Cor da borda esquerda do cartão
        delta: Valor de variação (opcional)
        help_text: Texto de ajuda (opcional)
    """
    # Determinar cor para o delta, se fornecido
    delta_color = ""
    delta_arrow = ""
    
    if delta:
        try:
            delta_value = float(delta.replace("%", "").replace("+", ""))
            if delta_value > 0:
                delta_color = CORES["completo"]
                delta_arrow = "↑"
            elif delta_value < 0:
                delta_color = CORES["pendencia"]
                delta_arrow = "↓"
        except:
            pass
    
    # Ícone HTML
    icone_html = f'<span style="font-size: 20px;">{icone}</span>' if icone else ''
    
    # Help tooltip
    tooltip_attr = f'title="{help_text}"' if help_text else ''
    
    # Cartão HTML
    html = f"""
    <div style="background-color: white; padding: 15px; border-radius: 8px; 
         box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 15px; 
         border-left: 5px solid {cor};" {tooltip_attr}>
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <h3 style="margin: 0; font-size: 14px; color: #555;">{titulo}</h3>
            {icone_html}
        </div>
        <h2 style="margin: 10px 0; font-size: 28px; font-weight: 600;">{valor}</h2>
        
        {'' if not delta else f'<p style="margin: 0; color: {delta_color}; font-size: 14px; font-weight: 500;">{delta_arrow} {delta}</p>'}
    </div>
    """
    
    return st.markdown(html, unsafe_allow_html=True)

@contextmanager
def card_container(titulo: str):
    """
    Contextmanager para criar um container estilizado como card
    
    Args:
        titulo: Título do card
    """
    # Início do card
    html_inicio = f"""
    <div style="background-color: white; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); 
         padding: 15px; margin-bottom: 15px; height: 100%; display: flex; flex-direction: column;">
        <h3 style="margin-top: 0; margin-bottom: 10px; color: {CORES['azul_principal']}; 
            font-size: 16px; border-bottom: 1px solid {CORES['cinza_medio']}; padding-bottom: 8px;">
            {titulo}
        </h3>
        <div style="flex-grow: 1; display: flex; flex-direction: column;">
    """
    
    st.markdown(html_inicio, unsafe_allow_html=True)
    
    # Renderizar conteúdo
    yield
    
    # Fechamento do card
    html_fim = """
        </div>
    </div>
    """
    
    st.markdown(html_fim, unsafe_allow_html=True)

def formatar_tabela_pendencias(df: pd.DataFrame):
    """
    Formata e exibe uma tabela de pendências
    
    Args:
        df: DataFrame com os dados de pendências
    """
    # Aplicar estilo básico sem destaque colorido
    df_styled = df.style.set_table_styles([
        {'selector': 'thead th', 'props': f'background-color: {CORES["azul_principal"]}; color: white; padding: 8px 15px;'},
        {'selector': 'tbody tr:nth-child(even)', 'props': f'background-color: {CORES["cinza_claro"]};'},
        {'selector': 'tbody td', 'props': 'padding: 8px 15px;'}
    ])
    
    # Exibir o dataframe estilizado com título explícito
    st.subheader("Tabela de Pendências por Responsável")
    st.dataframe(df_styled, use_container_width=True, hide_index=True)
    return None

def formatar_tabela_status(df: pd.DataFrame):
    """
    Formata e exibe uma tabela de status
    
    Args:
        df: DataFrame com os dados de status
    """
    # Função para formatar células com status
    def formatar_status(val, col):
        if col == "% Concluído":
            return f"{val:.1f}%"
        return val
    
    # Aplicar estilo básico sem destaque colorido
    df_styled = df.style.set_table_styles([
        {'selector': 'thead th', 'props': f'background-color: {CORES["azul_principal"]}; color: white; padding: 8px 15px;'},
        {'selector': 'tbody tr:nth-child(even)', 'props': f'background-color: {CORES["cinza_claro"]};'},
        {'selector': 'tbody td', 'props': 'padding: 8px 15px;'}
    ])
    
    # Manter apenas a formatação de percentual sem cores
    if "% Concluído" in df.columns:
        df_styled = df_styled.format({"% Concluído": "{:.1f}%"})
    
    # Exibir o dataframe estilizado com título explícito
    st.subheader("Status da Higienização por Responsável")
    st.dataframe(df_styled, use_container_width=True, hide_index=True)
    return None

def formatar_tabela_produtividade(df: pd.DataFrame):
    """
    Formata e exibe uma tabela de produtividade
    
    Args:
        df: DataFrame com os dados de produtividade
    """
    # Aplicar estilo básico sem destaque colorido
    df_styled = df.style.set_table_styles([
        {'selector': 'thead th', 'props': f'background-color: {CORES["azul_principal"]}; color: white; padding: 8px 15px;'},
        {'selector': 'tbody tr:nth-child(even)', 'props': f'background-color: {CORES["cinza_claro"]};'},
        {'selector': 'tbody td', 'props': 'padding: 8px 15px;'}
    ])
    
    # Formatar a coluna de percentual
    if "% Produtividade" in df.columns:
        df_styled = df_styled.format({"% Produtividade": "{:.1f}%"})
    
    # Exibir o dataframe estilizado com título explícito
    st.subheader("Tabela de Produtividade por Responsável")
    st.dataframe(df_styled, use_container_width=True, hide_index=True)
    return None

def criar_filtro_responsaveis(df: pd.DataFrame, key: str = "filtro_responsaveis"):
    """
    Cria um filtro de múltipla escolha para responsáveis
    
    Args:
        df: DataFrame com os dados
        key: Chave única para o componente
        
    Returns:
        Lista de responsáveis selecionados
    """
    if "ASSIGNED_BY_NAME" not in df.columns:
        return None
    
    # Obter lista de responsáveis
    responsaveis = sorted(df["ASSIGNED_BY_NAME"].unique().tolist())
    
    # Criar o multiselect
    responsaveis_selecionados = st.multiselect(
        "Filtrar por Responsável:",
        options=["Todos"] + responsaveis,
        default=["Todos"],
        key=key
    )
    
    # Se "Todos" estiver selecionado, retornar todos os responsáveis
    if "Todos" in responsaveis_selecionados:
        return responsaveis
    
    return responsaveis_selecionados 
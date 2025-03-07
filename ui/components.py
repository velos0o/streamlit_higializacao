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
    Renderiza um cartão com métrica estilizado em design profissional
    
    Args:
        titulo: Título da métrica
        valor: Valor da métrica
        icone: Não utilizado mais (mantido para compatibilidade)
        cor: Cor de destaque do cartão
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
    
    # Help tooltip
    tooltip_attr = f'title="{help_text}"' if help_text else ''
    
    # HTML do cartão - estilo profissional com cinza e azul, sem emojis
    html = f"""
    <div style="background-color: white; padding: 18px 20px; border-radius: 4px; 
         box-shadow: 0 1px 4px rgba(0,0,0,0.08); margin-bottom: 15px; 
         border-top: 3px solid {CORES['azul_principal']};" {tooltip_attr}>
        <div>
            <h3 style="margin: 0; font-size: 13px; color: {CORES['cinza_escuro']}; font-weight: 500; letter-spacing: 0.3px;">{titulo.upper()}</h3>
        </div>
        <h2 style="margin: 10px 0 5px 0; font-size: 26px; font-weight: 600; color: {CORES['azul_principal']};">{valor}</h2>
        
        {f'<p style="margin: 0; color: {delta_color}; font-size: 13px; font-weight: 500;">{delta_arrow} {delta}</p>' if delta else ''}
    </div>
    """
    
    st.markdown(html, unsafe_allow_html=True)

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

def formatar_tabela_pendencias(df: pd.DataFrame, mostrar_titulo=False):
    """
    Formata e exibe uma tabela de pendências com design profissional
    
    Args:
        df: DataFrame com os dados de pendências
        mostrar_titulo: Se True, exibe o título da tabela (padrão: False)
    """
    # Verificar se é necessário adicionar uma linha de total
    if "Total" in df.columns and not df.index.isin(["Total"]).any():
        # Criar uma linha de total
        total_row = pd.DataFrame(
            {col: [df[col].sum() if pd.api.types.is_numeric_dtype(df[col]) else "Total"] 
             for col in df.columns},
            index=["Total"]
        )
        
        # Adicionar linha de total ao final do DataFrame
        df = pd.concat([df, total_row])
    
    # Estilo profissional com cores cinza e azul
    df_styled = df.style.set_table_styles([
        # Cabeçalho
        {'selector': 'thead th', 'props': f'background-color: {CORES["azul_principal"]}; color: white; padding: 12px 15px; font-weight: 500; font-size: 13px; text-align: left;'},
        # Linhas alternadas
        {'selector': 'tbody tr:nth-child(even)', 'props': f'background-color: {CORES["cinza_claro"]};'},
        # Todas as células
        {'selector': 'tbody td', 'props': f'padding: 10px 15px; border-bottom: 1px solid {CORES["cinza_medio"]}; font-size: 13px;'},
        # Linha de total
        {'selector': 'tbody tr:last-child', 'props': f'background-color: {CORES["cinza_medio"]}; font-weight: bold;'}
    ])
    
    # Destacar a linha de total com negrito para os valores numéricos
    if "Total" in df.index:
        for col in df.columns:
            if pd.api.types.is_numeric_dtype(df[col]) and col != "Total":
                df_styled = df_styled.apply(lambda x: ['font-weight: bold' if idx == 'Total' else '' for idx in x.index], axis=0, subset=[col])
    
    # Exibir o título apenas se solicitado
    if mostrar_titulo:
        st.subheader("Tabela de Pendências por Responsável")
        
    # Exibir o dataframe estilizado
    st.dataframe(df_styled, use_container_width=True, hide_index=False)
    return None

def formatar_tabela_status(df: pd.DataFrame, mostrar_titulo=False):
    """
    Formata e exibe uma tabela de status com design profissional
    
    Args:
        df: DataFrame com os dados de status
        mostrar_titulo: Se True, exibe o título da tabela (padrão: False)
    """
    # Verificar se é necessário adicionar uma linha de total
    if "Total" in df.columns and not df.index.isin(["Total"]).any():
        # Criar uma linha de total
        total_row = pd.DataFrame(
            {col: [df[col].sum() if pd.api.types.is_numeric_dtype(df[col]) else "Total"] 
             for col in df.columns},
            index=["Total"]
        )
        
        # Adicionar linha de total ao final do DataFrame
        df = pd.concat([df, total_row])
    
    # Estilo profissional com cores cinza e azul
    df_styled = df.style.set_table_styles([
        # Cabeçalho
        {'selector': 'thead th', 'props': f'background-color: {CORES["azul_principal"]}; color: white; padding: 12px 15px; font-weight: 500; font-size: 13px; text-align: left;'},
        # Linhas alternadas
        {'selector': 'tbody tr:nth-child(even)', 'props': f'background-color: {CORES["cinza_claro"]};'},
        # Todas as células
        {'selector': 'tbody td', 'props': f'padding: 10px 15px; border-bottom: 1px solid {CORES["cinza_medio"]}; font-size: 13px;'},
        # Linha de total
        {'selector': 'tbody tr:last-child', 'props': f'background-color: {CORES["cinza_medio"]}; font-weight: bold;'}
    ])
    
    # Manter apenas a formatação de percentual
    if "% Concluído" in df.columns:
        df_styled = df_styled.format({
            "% Concluído": lambda x: f"{x:.1f}%"
        })
    
    # Destacar a linha de total com negrito para os valores numéricos
    if "Total" in df.index:
        for col in df.columns:
            if pd.api.types.is_numeric_dtype(df[col]) and col != "Total":
                df_styled = df_styled.apply(lambda x: ['font-weight: bold' if idx == 'Total' else '' for idx in x.index], axis=0, subset=[col])
    
    # Exibir o título apenas se solicitado
    if mostrar_titulo:
        st.subheader("Status da Higienização por Responsável")
        
    # Exibir o dataframe estilizado
    st.dataframe(df_styled, use_container_width=True, hide_index=False)
    return None

def formatar_tabela_produtividade(df: pd.DataFrame, mostrar_titulo=False):
    """
    Formata e exibe uma tabela de produtividade com design profissional
    
    Args:
        df: DataFrame com os dados de produtividade
        mostrar_titulo: Se True, exibe o título da tabela (padrão: False)
    """
    # Verificar se é necessário adicionar uma linha de total
    if "Total" in df.columns and not df.index.isin(["Total"]).any():
        # Criar uma linha de total
        total_row = pd.DataFrame(
            {col: [df[col].sum() if pd.api.types.is_numeric_dtype(df[col]) else "Total"] 
             for col in df.columns},
            index=["Total"]
        )
        
        # Adicionar linha de total ao final do DataFrame
        df = pd.concat([df, total_row])
    
    # Estilo profissional com cores cinza e azul
    df_styled = df.style.set_table_styles([
        # Cabeçalho
        {'selector': 'thead th', 'props': f'background-color: {CORES["azul_principal"]}; color: white; padding: 12px 15px; font-weight: 500; font-size: 13px; text-align: left;'},
        # Linhas alternadas
        {'selector': 'tbody tr:nth-child(even)', 'props': f'background-color: {CORES["cinza_claro"]};'},
        # Todas as células
        {'selector': 'tbody td', 'props': f'padding: 10px 15px; border-bottom: 1px solid {CORES["cinza_medio"]}; font-size: 13px;'},
        # Linha de total
        {'selector': 'tbody tr:last-child', 'props': f'background-color: {CORES["cinza_medio"]}; font-weight: bold;'}
    ])
    
    # Destacar a linha de total com negrito para os valores numéricos
    if "Total" in df.index:
        for col in df.columns:
            if pd.api.types.is_numeric_dtype(df[col]) and col != "Total":
                df_styled = df_styled.apply(lambda x: ['font-weight: bold' if idx == 'Total' else '' for idx in x.index], axis=0, subset=[col])
    
    # Exibir o título apenas se solicitado
    if mostrar_titulo:
        st.subheader("Tabela de Produtividade por Responsável")
        
    # Exibir o dataframe estilizado
    st.dataframe(df_styled, use_container_width=True, hide_index=False)
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
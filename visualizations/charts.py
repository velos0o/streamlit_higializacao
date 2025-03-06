"""Visualizações para o dashboard de Higienização"""
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from config.settings import CORES
import streamlit as st

def grafico_status_pizza(df: pd.DataFrame):
    """
    Cria um gráfico de pizza com o status de higienização
    
    Args:
        df: DataFrame com os dados
        
    Returns:
        Figura do plotly
    """
    # Contagem de status
    status_counts = df["STATUS_CATEGORIA"].value_counts().reset_index()
    status_counts.columns = ["Status", "Quantidade"]
    
    # Definir cores para cada status
    colors_map = {
        "PENDENCIA": CORES["pendencia"],
        "INCOMPLETO": CORES["incompleto"],
        "COMPLETO": CORES["completo"]
    }
    
    fig = px.pie(
        status_counts, 
        values="Quantidade", 
        names="Status", 
        title="",
        color="Status",
        color_discrete_map=colors_map,
        hole=0.4
    )
    
    fig.update_layout(
        margin=dict(t=10, b=10, l=10, r=10),
        height=350,
        legend=dict(
            orientation="h",
            y=-0.1,
            x=0.5,
            xanchor="center"
        ),
        font=dict(
            family="Arial, sans-serif",
            size=12
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)"
    )
    
    return fig

def grafico_pendencias_horizontais(df: pd.DataFrame):
    """
    Cria um gráfico de barras horizontais com as pendências por campo
    
    Args:
        df: DataFrame com os dados
        
    Returns:
        Figura do plotly
    """
    # Contar pendências por campo
    pendencias = {
        "Requerimento": df["PENDENCIA_REQUERIMENTO"].sum(),
        "Documentação": df["PENDENCIA_DOCUMENTACAO"].sum(),
        "Cadastro Árvore": df["PENDENCIA_CADASTRO_ARVORE"].sum(),
        "Estrutura Árvore": df["PENDENCIA_ESTRUTURA_ARVORE"].sum()
    }
    
    # Criar DataFrame para plotar
    df_pendencias = pd.DataFrame({
        "Campo": list(pendencias.keys()),
        "Pendências": list(pendencias.values())
    })
    
    # Ordenar por quantidade
    df_pendencias = df_pendencias.sort_values("Pendências", ascending=True)
    
    fig = go.Figure(go.Bar(
        x=df_pendencias["Pendências"],
        y=df_pendencias["Campo"],
        orientation="h",
        marker=dict(
            color=CORES["pendencia"]
        ),
        text=df_pendencias["Pendências"],
        textposition="auto"
    ))
    
    fig.update_layout(
        title="",
        xaxis_title="",
        yaxis_title="",
        margin=dict(t=10, b=10, l=10, r=10),
        height=350,
        font=dict(
            family="Arial, sans-serif",
            size=12
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(
            showgrid=True,
            gridcolor="rgba(0,0,0,0.1)"
        ),
        yaxis=dict(
            showgrid=False
        )
    )
    
    return fig

def grafico_status_por_responsavel(df: pd.DataFrame):
    """
    Cria um gráfico de barras empilhadas com status por responsável
    
    Args:
        df: DataFrame com os dados
        
    Returns:
        Figura do plotly
    """
    # Contar status por responsável
    df_status = df.groupby(["ASSIGNED_BY_NAME", "STATUS_CATEGORIA"]).size().reset_index(name="count")
    
    # Definir cores para cada status
    colors_map = {
        "PENDENCIA": CORES["pendencia"],
        "INCOMPLETO": CORES["incompleto"],
        "COMPLETO": CORES["completo"]
    }
    
    fig = px.bar(
        df_status,
        x="ASSIGNED_BY_NAME",
        y="count",
        color="STATUS_CATEGORIA",
        title="",
        color_discrete_map=colors_map,
        text_auto=True
    )
    
    fig.update_layout(
        xaxis_title="Responsável",
        yaxis_title="Quantidade",
        legend_title="Status",
        legend=dict(
            orientation="h",
            y=1.02,
            x=0.5,
            xanchor="center"
        ),
        margin=dict(t=30, b=10, l=10, r=10),
        height=400,
        font=dict(
            family="Arial, sans-serif",
            size=12
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(
            tickangle=-45,
            showgrid=False
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor="rgba(0,0,0,0.1)"
        ),
        bargap=0.2
    )
    
    return fig

def grafico_progresso_gauge(valor_percentual: float):
    """
    Cria um gráfico de medidor (gauge) com o percentual de progresso
    
    Args:
        valor_percentual: Valor percentual a ser exibido
        
    Returns:
        Figura do plotly
    """
    # Determinar cor do medidor baseado no percentual
    if valor_percentual < 30:
        cor = CORES["pendencia"]
    elif valor_percentual < 70:
        cor = CORES["incompleto"]
    else:
        cor = CORES["completo"]
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=valor_percentual,
        domain={"x": [0, 1], "y": [0, 1]},
        title={"text": "Progresso Total", "font": {"size": 18}},
        gauge={
            "axis": {"range": [0, 100], "tickwidth": 1},
            "bar": {"color": cor},
            "steps": [
                {"range": [0, 30], "color": "rgba(255, 193, 7, 0.2)"},
                {"range": [30, 70], "color": "rgba(253, 126, 20, 0.2)"},
                {"range": [70, 100], "color": "rgba(40, 167, 69, 0.2)"}
            ],
            "threshold": {
                "line": {"color": "red", "width": 4},
                "thickness": 0.75,
                "value": 90
            }
        },
        number={"suffix": "%", "font": {"size": 26}}
    ))
    
    fig.update_layout(
        margin=dict(t=30, b=30, l=30, r=30),
        height=300,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(
            family="Arial, sans-serif",
            size=14
        )
    )
    
    return fig 
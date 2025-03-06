"""Processamento de dados para o dashboard de Higienização"""
import pandas as pd
import streamlit as st
from config.settings import CAMPOS_PERSONALIZADOS
from typing import Dict, List, Tuple, Any, Optional

def criar_tabela_pendencias(df: pd.DataFrame, responsaveis_filtrados: Optional[List[str]] = None) -> pd.DataFrame:
    """
    Cria uma tabela de pendências por responsável
    
    Args:
        df: DataFrame com os dados processados
        responsaveis_filtrados: Lista de responsáveis para filtrar (opcional)
        
    Returns:
        DataFrame formatado para a tabela de pendências
    """
    # Verificar se há dados para processar
    if df is None or df.empty:
        return pd.DataFrame()
    
    # Filtrar por responsáveis, se especificado
    if responsaveis_filtrados:
        df = df[df["ASSIGNED_BY_NAME"].isin(responsaveis_filtrados)]
    
    # Campos para analisar
    campos = {
        "REQUERIMENTO": "Requerimento",
        "DOCUMENTACAO": "Documentação",
        "CADASTRO_ARVORE": "Cadastro na Árvore",
        "ESTRUTURA_ARVORE": "Estrutura da Árvore",
        "EMISSOES_BRASILEIRAS": "Emissões Brasileiras"
    }
    
    # Inicializar listas para os dados da tabela
    rows = []
    
    # Para cada responsável, contar pendências por campo
    for responsavel in sorted(df["ASSIGNED_BY_NAME"].unique()):
        row = {"Responsável": responsavel}
        
        # Filtrar dados deste responsável
        df_resp = df[df["ASSIGNED_BY_NAME"] == responsavel]
        
        # Contar pendências para cada campo
        for campo_id, campo_nome in campos.items():
            status_col = f"{campo_id}_STATUS"
            # Contar registros com status 0 (pendente)
            row[campo_nome] = len(df_resp) - df_resp[status_col].sum()
        
        # Adicionar total de pendências
        row["Total"] = sum([row[campo] for campo in campos.values()])
        
        rows.append(row)
    
    # Criar DataFrame
    result = pd.DataFrame(rows)
    
    # Adicionar linha de totais
    if not result.empty:
        totals = {"Responsável": "TOTAL"}
        for col in result.columns[1:]:
            totals[col] = result[col].sum()
        
        result = pd.concat([result, pd.DataFrame([totals])], ignore_index=True)
    
    return result

def criar_tabela_status_higienizacao(df: pd.DataFrame, responsaveis_filtrados: Optional[List[str]] = None) -> pd.DataFrame:
    """
    Cria uma tabela de status de higienização por responsável
    
    Args:
        df: DataFrame com os dados processados
        responsaveis_filtrados: Lista de responsáveis para filtrar (opcional)
        
    Returns:
        DataFrame formatado para a tabela de status
    """
    # Verificar se há dados para processar
    if df is None or df.empty:
        return pd.DataFrame()
    
    # Filtrar por responsáveis, se especificado
    if responsaveis_filtrados:
        df = df[df["ASSIGNED_BY_NAME"].isin(responsaveis_filtrados)]
    
    # Inicializar listas para os dados da tabela
    rows = []
    
    # Para cada responsável, contar por categoria de status
    for responsavel in sorted(df["ASSIGNED_BY_NAME"].unique()):
        row = {"Responsável": responsavel}
        
        # Filtrar dados deste responsável
        df_resp = df[df["ASSIGNED_BY_NAME"] == responsavel]
        total_resp = len(df_resp)
        
        # Contar por status
        status_counts = df_resp["STATUS_CATEGORIA"].value_counts()
        
        row["PENDENCIA"] = status_counts.get("PENDENCIA", 0)
        row["INCOMPLETO"] = status_counts.get("INCOMPLETO", 0)
        row["COMPLETO"] = status_counts.get("COMPLETO", 0)
        row["Total"] = total_resp
        
        # Calcular percentual concluído
        row["% Concluído"] = (row["COMPLETO"] / total_resp * 100) if total_resp > 0 else 0
        
        rows.append(row)
    
    # Criar DataFrame
    result = pd.DataFrame(rows)
    
    # Renomear colunas para exibição
    result = result.rename(columns={
        "PENDENCIA": "Pendências",
        "INCOMPLETO": "Incompletos",
        "COMPLETO": "Concluídos"
    })
    
    # Adicionar linha de totais
    if not result.empty:
        total_registros = len(df)
        status_total = df["STATUS_CATEGORIA"].value_counts()
        
        totals = {
            "Responsável": "TOTAL",
            "Pendências": status_total.get("PENDENCIA", 0),
            "Incompletos": status_total.get("INCOMPLETO", 0),
            "Concluídos": status_total.get("COMPLETO", 0),
            "Total": total_registros,
            "% Concluído": (status_total.get("COMPLETO", 0) / total_registros * 100) if total_registros > 0 else 0
        }
        
        result = pd.concat([result, pd.DataFrame([totals])], ignore_index=True)
    
    return result

def criar_tabela_produtividade(df: pd.DataFrame, responsaveis_filtrados: Optional[List[str]] = None) -> pd.DataFrame:
    """
    Cria uma tabela de produtividade por responsável (inverso da tabela de pendências)
    
    Args:
        df: DataFrame com os dados processados
        responsaveis_filtrados: Lista de responsáveis para filtrar (opcional)
        
    Returns:
        DataFrame formatado para a tabela de produtividade
    """
    # Verificar se há dados para processar
    if df is None or df.empty:
        return pd.DataFrame()
    
    # Filtrar por responsáveis, se especificado
    if responsaveis_filtrados:
        df = df[df["ASSIGNED_BY_NAME"].isin(responsaveis_filtrados)]
    
    # Campos para analisar
    campos = {
        "REQUERIMENTO": "Requerimento",
        "DOCUMENTACAO": "Documentação",
        "CADASTRO_ARVORE": "Cadastro na Árvore",
        "ESTRUTURA_ARVORE": "Estrutura da Árvore",
        "EMISSOES_BRASILEIRAS": "Emissões Brasileiras"
    }
    
    # Inicializar listas para os dados da tabela
    rows = []
    
    # Para cada responsável, contar itens concluídos por campo
    for responsavel in sorted(df["ASSIGNED_BY_NAME"].unique()):
        row = {"Responsável": responsavel}
        
        # Filtrar dados deste responsável
        df_resp = df[df["ASSIGNED_BY_NAME"] == responsavel]
        total_registros = len(df_resp)
        
        # Contar itens concluídos para cada campo
        for campo_id, campo_nome in campos.items():
            status_col = f"{campo_id}_STATUS"
            # Contar registros com status 1 (concluído)
            row[campo_nome] = df_resp[status_col].sum()
        
        # Adicionar total de itens concluídos
        row["Total"] = sum([row[campo] for campo in campos.values()])
        
        # Adicionar percentual de produtividade
        max_possiveis = total_registros * len(campos)
        row["% Produtividade"] = (row["Total"] / max_possiveis * 100) if max_possiveis > 0 else 0
        
        rows.append(row)
    
    # Criar DataFrame
    result = pd.DataFrame(rows)
    
    # Adicionar linha de totais
    if not result.empty:
        totals = {"Responsável": "TOTAL"}
        for col in result.columns[1:]:
            if col != "% Produtividade":
                totals[col] = result[col].sum()
        
        # Calcular percentual total de produtividade
        total_registros = len(df)
        max_possiveis = total_registros * len(campos)
        totals["% Produtividade"] = (totals["Total"] / max_possiveis * 100) if max_possiveis > 0 else 0
        
        result = pd.concat([result, pd.DataFrame([totals])], ignore_index=True)
    
    return result

def filtrar_dados(df: pd.DataFrame, responsaveis: List[str] = None) -> pd.DataFrame:
    """
    Filtra os dados com base nos critérios especificados
    
    Args:
        df: DataFrame original
        responsaveis: Lista de responsáveis para filtrar
        
    Returns:
        DataFrame filtrado
    """
    if df is None or df.empty:
        return df
    
    # Filtrar por responsáveis
    if responsaveis:
        df = df[df["ASSIGNED_BY_NAME"].isin(responsaveis)]
    
    return df 
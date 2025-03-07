"""
Relatório de Higienização - Bitrix24

Este relatório permite monitorar o status de higienização de registros no Bitrix24,
incluindo pendências e progresso por responsável.

Autor: Equipe de Desenvolvimento
Versão: 1.0.0
"""
import streamlit as st
import pandas as pd
import time
import sys
import os
import platform
import base64
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Any
from datetime import datetime, timedelta
from io import BytesIO
import re

# Importar módulos do projeto
from config.settings import CATEGORY_ID, CONFIG_VERIFICADA, CORES, CAMPOS_PERSONALIZADOS, BASE_PATH
from data.bitrix_service import BitrixService
from data.processor import criar_tabela_pendencias, criar_tabela_status_higienizacao, criar_tabela_produtividade, filtrar_dados
from ui.components import cabecalho, cartao_metrica, card_container, formatar_tabela_pendencias, formatar_tabela_status, formatar_tabela_produtividade, criar_filtro_responsaveis

# Configuração da página - DEVE ser a primeira chamada Streamlit
st.set_page_config(
    page_title="Relatório de Higienização",
    page_icon="logo.svg.svg",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Aplicar estilo CSS
def aplicar_estilo():
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
            
            /* Estilo do menu horizontal */
            div[data-testid="stHorizontalBlock"] {{
                background: white;
                padding: 1rem;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                margin-bottom: 1.5rem;
            }}
            
            /* Estilo dos botões do menu */
            div[data-testid="stHorizontalBlock"] .stRadio {{
                display: flex;
                gap: 2rem;
                justify-content: center;
            }}
            
            div[data-testid="stHorizontalBlock"] .stRadio > label {{
                background: #f8f9fa;
                padding: 0.8rem 1.5rem;
                border-radius: 6px;
                cursor: pointer;
                transition: all 0.3s ease;
                border: 1px solid #e9ecef;
            }}
            
            div[data-testid="stHorizontalBlock"] .stRadio > label:hover {{
                background: #e9ecef;
                transform: translateY(-2px);
            }}
            
            div[data-testid="stHorizontalBlock"] .stRadio input:checked + label {{
                background: #0083B8;
                color: white;
                border-color: #0083B8;
            }}
            
            /* Ocultar o círculo do radio button */
            div[data-testid="stHorizontalBlock"] .stRadio input {{
                display: none;
            }}
            
            /* Estilo da tabela */
            .dataframe {{
                width: 100%;
                margin-top: 1rem;
                background: white;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            
            /* Cabeçalho */
            .header-container {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 1rem;
                padding: 1rem;
                background-color: {CORES['azul_principal']};
                border-radius: 10px;
                color: white;
            }}
            
            /* Cartões */
            .card {{
                background-color: white;
                padding: 1.5rem;
                border-radius: 10px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                margin-bottom: 1rem;
            }}
            
            /* Métricas */
            .metric-card {{
                background-color: white;
                padding: 1rem;
                border-radius: 8px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                margin-bottom: 1rem;
                text-align: center;
                transition: transform 0.3s ease;
            }}
            
            .metric-card:hover {{
                transform: translateY(-5px);
                box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            }}
            
            .metric-value {{
                font-size: 2rem;
                font-weight: bold;
                margin: 0.5rem 0;
            }}
            
            .metric-title {{
                font-size: 1rem;
                color: #6c757d;
                margin: 0;
            }}
            
            .metric-icon {{
                font-size: 1.5rem;
                margin-bottom: 0.5rem;
            }}
            
            /* Tabelas */
            .dataframe th {{
                background-color: {CORES['azul_principal']};
                color: white;
                padding: 0.75rem;
                text-align: left;
            }}
            
            .dataframe td {{
                padding: 0.75rem;
                border-bottom: 1px solid #dee2e6;
            }}
            
            .dataframe tr:nth-child(even) {{
                background-color: #f8f9fa;
            }}
            
            .dataframe tr:hover {{
                background-color: #e9ecef;
            }}
            
            /* Formatação específica para última linha (totais) */
            .dataframe tr:last-child {{
                font-weight: bold;
                background-color: #e9ecef;
            }}
            
            /* Status */
            .status {{
                padding: 0.25rem 0.5rem;
                border-radius: 4px;
                font-size: 0.875rem;
                font-weight: 500;
                display: inline-block;
            }}
            
            .status-pendente {{
                background-color: #ffcccc;
                color: #dc3545;
            }}
            
            .status-incompleto {{
                background-color: #fff3cd;
                color: #856404;
            }}
            
            .status-completo {{
                background-color: #d1e7dd;
                color: #0f5132;
            }}
        </style>
    """
    st.markdown(estilo, unsafe_allow_html=True)

# Inicializar serviço do Bitrix
service = BitrixService()

# Função para configurar o ID da categoria
def configurar_categoria():
    """Função para configurar o ID da categoria no arquivo settings.py e mostrar diagnóstico"""
    st.title("Configurações do Dashboard")
    
    # Usar tabs para separar configuração e diagnóstico
    tab1, tab2 = st.tabs(["Configuração de Categoria", "Diagnóstico"])
    
    with tab1:
        # Exibir o valor atual
        st.write(f"O ID da categoria atual é: **{CATEGORY_ID}**")
        
        # Explicação
        st.write("""
        ## Como obter o ID da categoria no Bitrix24
        
        1. Acesse o Bitrix24 e vá para o módulo CRM
        2. Clique em "Negócios" e selecione a categoria desejada
        3. Observe a URL no navegador, o ID da categoria aparece após "CATEGORY_ID="
        4. Por exemplo, na URL ".../crm/deal/category/32/", o ID da categoria é 32
        """)
        
        # Entrada para o novo valor
        novo_id = st.number_input(
            "Digite o ID da categoria:",
            min_value=0,
            value=CATEGORY_ID,
            step=1,
            format="%d"
        )
        
        # Botões de ação
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Salvar", type="primary"):
                # Atualizar o arquivo settings.py
                try:
                    # Ler o arquivo
                    with open("config/settings.py", "r") as f:
                        content = f.read()
                    
                    # Atualizar o valor da categoria
                    import re
                    content = re.sub(
                        r'CATEGORY_ID\s*=\s*\d+',
                        f'CATEGORY_ID = {novo_id}',
                        content
                    )
                    
                    # Atualizar o valor de verificação
                    content = re.sub(
                        r'CONFIG_VERIFICADA\s*=\s*(True|False)',
                        'CONFIG_VERIFICADA = True',
                        content
                    )
                    
                    # Escrever de volta no arquivo
                    with open("config/settings.py", "w") as f:
                        f.write(content)
                    
                    # Feedback
                    st.success(f"ID da categoria atualizado para {novo_id} com sucesso!")
                    time.sleep(2)
                    
                    # Recarregar a página
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"Erro ao atualizar o arquivo: {str(e)}")
        
        with col2:
            if st.button("Pular Verificação"):
                # Apenas marcar como verificado sem alterar o ID
                try:
                    # Ler o arquivo
                    with open("config/settings.py", "r") as f:
                        content = f.read()
                    
                    # Atualizar o valor de verificação
                    content = re.sub(
                        r'CONFIG_VERIFICADA\s*=\s*(True|False)',
                        'CONFIG_VERIFICADA = True',
                        content
                    )
                    
                    # Escrever de volta no arquivo
                    with open("config/settings.py", "w") as f:
                        f.write(content)
                    
                    # Feedback
                    st.success("Verificação concluída com sucesso!")
                    time.sleep(2)
                    
                    # Recarregar a página
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"Erro ao atualizar o arquivo: {str(e)}")
        
        # Botão para voltar
        if st.button("Voltar para o Dashboard"):
            st.rerun()
    
    # Se a opção de diagnóstico estiver habilitada, exiba a tab de diagnóstico
    with tab2:
        if st.session_state.get("incluir_diagnostico", False):
            # Incorporar a função de diagnóstico aqui
            st.subheader("Diagnóstico do Sistema")
            st.write("Informações sobre o ambiente e configurações:")
            
            # Informações do sistema
            st.code(f"""
            Sistema: {platform.system()} {platform.release()}
            Python: {sys.version}
            Diretório: {os.getcwd()}
            """)
            
            # Informações do Bitrix
            st.write("### Configurações do Bitrix24")
            st.write(f"ID da Categoria: {CATEGORY_ID}")
            st.write(f"Verificada: {CONFIG_VERIFICADA}")
            
            # Logs de depuração
            if 'bitrix_debug' in st.session_state and st.session_state['bitrix_debug']:
                st.write("### Logs de Debug")
                for log in st.session_state['bitrix_debug']:
                    st.text(log)
            else:
                st.info("Nenhum log de debug disponível. Execute uma operação para gerar logs.")
        
        # Resetar o estado após mostrar
        st.session_state["incluir_diagnostico"] = False

# Função principal
def main():
    """Função principal da aplicação"""
    # Aplicar estilo CSS
    aplicar_estilo()
    
    # Exibir cabeçalho
    cabecalho()
    
    # Inicializar o estado da sessão para logs de debug se não existir
    if 'bitrix_debug' not in st.session_state:
        st.session_state['bitrix_debug'] = []
    
    # Verificar se a configuração está validada e o ID de categoria não é zero
    if not CONFIG_VERIFICADA or CATEGORY_ID == 0:
        configurar_categoria()
        return
    
    # Verificar se deve mostrar a tela de configuração
    if st.session_state.get("mostrar_config_categoria", False):
        configurar_categoria()
        # Resetar o estado após mostrar
        st.session_state["mostrar_config_categoria"] = False
        return
    
    # Verificar se os dados já foram carregados ou se precisam ser atualizados
    dados_precisam_atualizar = st.session_state.get('atualizar_dados', True)
    
    if 'dados_processados' not in st.session_state or dados_precisam_atualizar:
        # Obter dados (a barra de progresso agora está integrada dentro da função obter_dados_negocios)
        dados_brutos = obter_dados_negocios()
        
        if dados_brutos:
            try:
                # Criar elemento para mostrar progresso do processamento
                progress_proc = st.progress(0)
                status_proc = st.empty()
                status_proc.info("Processando dados obtidos...")
                
                # Processar dados
                progress_proc.progress(30)
                df = processar_dados_para_dashboard(dados_brutos)
                
                # Atualizar progresso
                progress_proc.progress(70)
                status_proc.info("Finalizando processamento...")
                
                # Armazenar dados processados
                st.session_state['dados_processados'] = df
                st.session_state['atualizar_dados'] = False  # Marcar como atualizado
                
                # Finalizar progresso
                progress_proc.progress(100)
                status_proc.success("Dados processados com sucesso!")
                
                # Limpar mensagem após 2 segundos
                time.sleep(2)
                status_proc.empty()
                progress_proc.empty()
                
            except Exception as e:
                st.error(f"Erro ao processar dados: {str(e)}")
                st.error("Detalhes do erro:")
                st.exception(e)
                
                # Mostrar informações sobre o formato dos dados para debug
                with st.expander("Informações sobre os dados recebidos"):
                    st.write(f"Tipo de dados: {type(dados_brutos)}")
                    if isinstance(dados_brutos, dict):
                        st.write(f"Chaves no dicionário: {list(dados_brutos.keys())}")
                    elif isinstance(dados_brutos, list):
                        st.write(f"Tamanho da lista: {len(dados_brutos)}")
                        if len(dados_brutos) > 0:
                            st.write("Primeira linha (cabeçalho):")
                            st.write(dados_brutos[0])
                        if len(dados_brutos) > 1:
                            st.write("Segunda linha (exemplo de dados):")
                            st.write(dados_brutos[1])
                return
        else:
            st.warning("Não foi possível obter dados do Bitrix24.")
            return
    
    # Recuperar dados processados da sessão
    df = st.session_state.get('dados_processados')
    
    if df is None or df.empty:
        st.warning("Não há dados disponíveis para exibir.")
        return
    
    # Filtros na barra lateral
    with st.sidebar:
        st.subheader("Filtros")
        
        # Usar todos os responsáveis disponíveis no DataFrame
        # Nenhum filtro de responsáveis permitidos
        df_filtrado = df.copy()
        
        # Manter o filtro existente para seleção adicional
        responsaveis_selecionados = criar_filtro_responsaveis(df_filtrado)
        
        # Mostrar categoria atual
        st.info(f"Categoria: {CATEGORY_ID}")
        
        # Adicionar um espaçador para empurrar as configurações para baixo
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Link para configurações com senha - movido para baixo
        st.markdown("---")
        st.markdown("### Configurações")
        senha = st.text_input("Senha", type="password")
        if st.button("Acessar Configurações"):
            if senha == "BatataFrita":
                st.session_state["mostrar_config_categoria"] = True
                # Também incluímos acesso ao diagnóstico na mesma área
                st.session_state["incluir_diagnostico"] = True
                st.rerun()
            else:
                st.error("Senha incorreta!")
        
        # Botão para atualizar dados
        if st.button("Atualizar Dados"):
            st.session_state['atualizar_dados'] = True
            st.rerun()  # Força rerun do script para atualizar dados
    
    # Exibir KPIs
    col1, col2, col3, col4 = st.columns(4)
    
    # Total de registros
    with col1:
        total_registros = len(df_filtrado)
        cartao_metrica("Total de Registros", f"{total_registros}")
    
    # Total de pendências
    with col2:
        total_pendencias = df_filtrado[df_filtrado["STATUS_CATEGORIA"] == "PENDENCIA"].shape[0]
        cartao_metrica("Pendências", f"{total_pendencias}")
    
    # Total em processo
    with col3:
        total_incompleto = df_filtrado[df_filtrado["STATUS_CATEGORIA"] == "INCOMPLETO"].shape[0]
        cartao_metrica("Incompletos", f"{total_incompleto}")
    
    # Total concluídos
    with col4:
        total_completo = df_filtrado[df_filtrado["STATUS_CATEGORIA"] == "COMPLETO"].shape[0]
        perc_completo = (total_completo / total_registros * 100) if total_registros > 0 else 0
        cartao_metrica("Concluídos", f"{total_completo} ({perc_completo:.1f}%)")
    
    # Informação sobre registros filtrados vs total
    total_geral = len(df)
    if total_registros != total_geral:
        st.info(f"Exibindo {total_registros} de {total_geral} registros ({(total_registros/total_geral*100):.1f}%)")
    
    # Separador antes das tabelas
    st.markdown("<hr style='margin: 30px 0px; border-top: 1px solid #ddd;'>", unsafe_allow_html=True)
    
    # CSS personalizado para o menu lateral e conteúdo
    st.markdown("""
    <style>
        /* Estilo para botões do menu lateral */
        .menu-lateral .stRadio [role="radiogroup"] {
            display: flex;
            flex-direction: column;
            gap: 30px;  /* Espaçamento aumentado entre itens */
            margin-top: 20px;
        }
        
        .menu-lateral .stRadio label {
            background-color: #f5f5f5;
            border-left: 5px solid transparent;
            padding: 18px 20px;
            border-radius: 5px;
            transition: all 0.3s;
            font-weight: 500;
            font-size: 16px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.05);
            margin-bottom: 15px;
        }
        
        .menu-lateral .stRadio label:hover {
            background-color: #e8e8e8;
            cursor: pointer;
            border-left-color: #b0d0ef;
            transform: translateX(5px);
        }
        
        .menu-lateral .stRadio [data-baseweb="radio"] input:checked + div + div {
            background-color: #0063B2;
            color: white;
            border-left: 5px solid #003f75;
            box-shadow: 0 3px 8px rgba(0,99,178,0.2);
        }
        
        /* Esconder o botão de rádio e deixar apenas o texto */
        .menu-lateral .stRadio [data-baseweb="radio"] div:first-child {
            display: none !important;
        }
        
        .menu-lateral .stRadio [data-baseweb="radio"] [data-testid="stMarkdownContainer"] {
            margin-left: 0;
            padding: 0;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Adicionar título principal de Análise de Dados
    st.markdown("<h3 style='color: #0063B2; margin-bottom: 20px;'>Análise de Dados por Responsável</h3>", unsafe_allow_html=True)
    
    # Preparar todas as tabelas antecipadamente
    try:
        tabela_pendencias = criar_tabela_pendencias(df_filtrado)
        tabela_status = criar_tabela_status_higienizacao(df_filtrado)
        tabela_produtividade = criar_tabela_produtividade(df_filtrado)
        
        # Menu horizontal
        opcao_tabela = st.radio(
            "",
            ["Tabela de Pendências", "Status da Higienização", "Tabela de Produtividade"],
            key="menu_horizontal_analise",
            label_visibility="collapsed",
            horizontal=True
        )
        
        # Adicionar um título para a tabela selecionada
        st.markdown(f"<h4 style='color: #555; margin-bottom: 15px;'>{opcao_tabela}</h4>", unsafe_allow_html=True)
        
        # Exibir a tabela selecionada
        if opcao_tabela == "Tabela de Pendências":
            formatar_tabela_pendencias(tabela_pendencias, mostrar_titulo=False)
        elif opcao_tabela == "Status da Higienização":
            formatar_tabela_status(tabela_status, mostrar_titulo=False)
        else:  # Tabela de Produtividade
            formatar_tabela_produtividade(tabela_produtividade, mostrar_titulo=False)

    except KeyError as e:
        st.error(f"Erro ao criar tabelas: Coluna {e} não encontrada nos dados. Verifique se os campos personalizados estão configurados corretamente.")
        # Mostrar as colunas disponíveis para ajudar na depuração
        st.info(f"Colunas disponíveis: {', '.join(df_filtrado.columns)}")
    except Exception as e:
        st.error(f"Erro ao criar tabelas: {str(e)}")
    
    # Rodapé
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: #6c757d;'>"
        "Relatório de Pendências e Status de Higienização | Bitrix24"
        "</div>",
        unsafe_allow_html=True
    )

# Função para obter dados de negócios com tratamento de erros aprimorado
def obter_dados_negocios():
    """Obtém os dados de negócios do Bitrix24 com tratamento de erros aprimorado"""
    try:
        # Verificar se há dados em cache
        if 'get_negocios' in st.session_state:
            return st.session_state['get_negocios']
        
        # Criar elementos para barra de progresso e mensagem de status
        progress_bar = st.progress(0)
        status_msg = st.empty()
        
        # Iniciar processo de carregamento
        status_msg.info("Iniciando conexão com Bitrix24...")
        progress_bar.progress(10)
        
        # 1. Consultar crm_deal (negócios da categoria especificada)
        filtros_deal = {
            "dimensionsFilters": [[
                {
                    "fieldName": "CATEGORY_ID",
                    "values": [CATEGORY_ID],
                    "type": "INCLUDE",
                    "operator": "EQUALS"
                }
            ]]
        }
        
        # Atualizar status
        status_msg.info("Carregando negócios da categoria selecionada...")
        progress_bar.progress(30)
        
        # Consultar dados de negócios
        deals_data = service.consultar_bitrix("crm_deal", filtros=filtros_deal)
        
        if not deals_data:
            status_msg.error("Não foi possível obter os dados de negócios")
            progress_bar.progress(100)  # Finalizar barra mesmo com erro
            return None
        
        # Atualizar progresso
        status_msg.info("Processando dados de negócios...")
        progress_bar.progress(50)
        
        # Log para debug
        debug_info = {
            "timestamp": pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S'),
            "table": "crm_deal",
            "filtros": filtros_deal,
            "sucesso": True,
            "mensagem": "Dados obtidos com sucesso",
            "detalhes": {"tamanho": len(deals_data) if isinstance(deals_data, list) else "N/A"}
        }
        if 'bitrix_debug' not in st.session_state:
            st.session_state['bitrix_debug'] = []
        st.session_state['bitrix_debug'].append(debug_info)
        
        # Verificar formato dos dados
        if isinstance(deals_data, list) and len(deals_data) > 1:
            # Converter para DataFrame
            deals_df = pd.DataFrame(deals_data[1:], columns=deals_data[0])
            
            # Atualizar progresso
            status_msg.info("Carregando campos personalizados...")
            progress_bar.progress(60)
            
            # 2. Consultar campos personalizados (crm_deal_uf) apenas para os IDs encontrados
            if not deals_df.empty:
                # Extrair IDs de negócios
                deal_ids = deals_df["ID"].tolist()
                
                # Preparar filtro para campos personalizados
                filtros_uf = {
                    "dimensionsFilters": [[
                        {
                            "fieldName": "DEAL_ID",
                            "values": deal_ids,
                            "type": "INCLUDE",
                            "operator": "EQUALS"
                        }
                    ]]
                }
                
                # Atualizar status
                status_msg.info(f"Obtendo campos personalizados para {len(deal_ids)} negócios...")
                progress_bar.progress(70)
                
                # Consultar campos personalizados
                uf_data = service.consultar_bitrix("crm_deal_uf", filtros=filtros_uf)
                
                # Log de campos personalizados para debug
                debug_info_uf = {
                    "timestamp": pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S'),
                    "table": "crm_deal_uf",
                    "filtros": filtros_uf,
                    "sucesso": bool(uf_data),
                    "mensagem": "Campos personalizados obtidos" if uf_data else "Erro ao obter campos personalizados",
                    "detalhes": {"tamanho": len(uf_data) if isinstance(uf_data, list) else "N/A"}
                }
                st.session_state['bitrix_debug'].append(debug_info_uf)
                
                # 3. Preparar dados combinados para o dashboard
                if uf_data and isinstance(uf_data, list) and len(uf_data) > 1:
                    # Atualizar status
                    status_msg.info("Combinando dados e preparando para exibição...")
                    progress_bar.progress(85)
                    
                    # Converter campos personalizados para DataFrame
                    uf_df = pd.DataFrame(uf_data[1:], columns=uf_data[0])
                    
                    # Mesclar os dados
                    # Nota: Os dados já serão processados em processar_dados_para_dashboard
                    dados_combinados = {
                        "deals": deals_data,
                        "uf_fields": uf_data
                    }
                    
                    # Armazenar em cache na sessão
                    st.session_state['get_negocios'] = dados_combinados
                    
                    # Finalizar com sucesso
                    progress_bar.progress(100)
                    status_msg.success(f"Dados carregados com sucesso: {len(deals_df)} negócios e seus campos personalizados")
                    
                    # Limpar mensagem após 3 segundos
                    time.sleep(2)
                    status_msg.empty()
                    
                    return dados_combinados
                else:
                    # Retornar apenas os negócios se não conseguir obter campos personalizados
                    progress_bar.progress(100)
                    status_msg.warning("Não foi possível obter os campos personalizados. Exibindo apenas dados básicos dos negócios.")
                    st.session_state['get_negocios'] = deals_data
                    
                    # Limpar mensagem após 3 segundos
                    time.sleep(2)
                    status_msg.empty()
                    
                    return deals_data
            else:
                # DataFrame vazio
                progress_bar.progress(100)
                status_msg.warning("Nenhum negócio encontrado na categoria selecionada")
                
                # Limpar mensagem após 3 segundos
                time.sleep(2)
                status_msg.empty()
                
                return None
        else:
            # Formato inesperado ou vazio
            progress_bar.progress(100)
            status_msg.error(f"Formato de dados inesperado: {type(deals_data)}")
            
            # Limpar mensagem após 3 segundos
            time.sleep(2)
            status_msg.empty()
            
            return None
                
    except Exception as e:
        # Log do erro para debug
        debug_info = {
            "timestamp": pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S'),
            "table": "multiple",
            "sucesso": False,
            "mensagem": f"Erro ao obter dados: {str(e)}",
            "detalhes": {"erro": str(e), "tipo": type(e).__name__}
        }
        if 'bitrix_debug' not in st.session_state:
            st.session_state['bitrix_debug'] = []
        st.session_state['bitrix_debug'].append(debug_info)
        
        # Se houver elementos de progresso criados
        try:
            progress_bar.progress(100)
            status_msg.error(f"Erro ao obter dados: {str(e)}")
        except:
            st.error(f"Erro ao obter dados: {str(e)}")
        
        return None

def processar_dados_para_dashboard(dados):
    """
    Processa os dados brutos do Bitrix24 para o formato usado no dashboard
    
    Args:
        dados: Dados brutos do Bitrix24 (pode ser lista ou dicionário com as tabelas combinadas)
        
    Returns:
        DataFrame com os dados processados
    """
    # Registro de informações para debug
    debug_info = {
        "timestamp": pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S'),
        "tipo_dados": type(dados).__name__,
        "sucesso": False,
        "mensagem": "",
        "detalhes": {}
    }
    
    # Verificar formato dos dados
    if dados is None:
        debug_info["mensagem"] = "Dados recebidos são None"
        if 'bitrix_debug' in st.session_state:
            st.session_state['bitrix_debug'].append(debug_info)
        return pd.DataFrame()
    
    # Caso 1: Formato combinado de deals e campos personalizados
    if isinstance(dados, dict) and "deals" in dados and "uf_fields" in dados:
        debug_info["detalhes"]["formato"] = "combinado"
        
        # Processar dados de negócios
        deals_data = dados["deals"]
        uf_data = dados["uf_fields"]
        
        try:
            # Criar DataFrame de negócios
            if len(deals_data) > 1:
                deals_df = pd.DataFrame(deals_data[1:], columns=deals_data[0])
                
                # Criar DataFrame de campos personalizados
                if len(uf_data) > 1:
                    uf_df = pd.DataFrame(uf_data[1:], columns=uf_data[0])
                    
                    # Mesclar os DataFrames
                    df_completo = pd.merge(
                        deals_df,
                        uf_df,
                        left_on="ID",
                        right_on="DEAL_ID",
                        how="left"
                    )
                    
                    debug_info["sucesso"] = True
                    debug_info["mensagem"] = "Dados combinados processados com sucesso"
                    debug_info["detalhes"]["num_registros"] = len(df_completo)
                    debug_info["detalhes"]["colunas"] = df_completo.columns.tolist()
                    
                    if 'bitrix_debug' in st.session_state:
                        st.session_state['bitrix_debug'].append(debug_info)
                    
                    # Processamento adicional
                    return _processar_campos_dataframe(df_completo)
                else:
                    # Se não houver dados de campos personalizados, usar só os negócios
                    debug_info["mensagem"] = "Usando apenas dados de negócios (sem campos personalizados)"
                    if 'bitrix_debug' in st.session_state:
                        st.session_state['bitrix_debug'].append(debug_info)
                    return _processar_campos_dataframe(deals_df)
            else:
                debug_info["mensagem"] = "Dados de negócios vazios ou inválidos"
                if 'bitrix_debug' in st.session_state:
                    st.session_state['bitrix_debug'].append(debug_info)
                return pd.DataFrame()
        except Exception as e:
            debug_info["sucesso"] = False
            debug_info["mensagem"] = f"Erro ao processar dados combinados: {str(e)}"
            debug_info["detalhes"]["erro"] = str(e)
            if 'bitrix_debug' in st.session_state:
                st.session_state['bitrix_debug'].append(debug_info)
            return pd.DataFrame()
    
    # Caso 2: Formato de lista (apenas negócios)
    elif isinstance(dados, list):
        debug_info["detalhes"]["formato"] = "lista"
        debug_info["detalhes"]["tamanho"] = len(dados)
        
        # Verificar se há dados suficientes
        if not dados or len(dados) <= 1:  # Só cabeçalho ou vazio
            debug_info["mensagem"] = "Lista vazia ou apenas cabeçalho"
            if 'bitrix_debug' in st.session_state:
                st.session_state['bitrix_debug'].append(debug_info)
            return pd.DataFrame()
            
        # Extrair cabeçalhos (primeira linha)
        headers = dados[0]
        debug_info["detalhes"]["colunas"] = headers
        
        try:
            # Criar DataFrame
            df = pd.DataFrame(dados[1:], columns=headers)
            debug_info["sucesso"] = True
            debug_info["mensagem"] = "Dados processados com sucesso (formato lista)"
            if 'bitrix_debug' in st.session_state:
                st.session_state['bitrix_debug'].append(debug_info)
            
            # Processamento adicional
            return _processar_campos_dataframe(df)
        except Exception as e:
            debug_info["sucesso"] = False
            debug_info["mensagem"] = f"Erro ao criar DataFrame: {str(e)}"
            if 'bitrix_debug' in st.session_state:
                st.session_state['bitrix_debug'].append(debug_info)
            return pd.DataFrame()
    
    # Caso 3: Outro formato não suportado
    else:
        debug_info["mensagem"] = f"Formato de dados não suportado: {type(dados).__name__}"
        if 'bitrix_debug' in st.session_state:
            st.session_state['bitrix_debug'].append(debug_info)
        return pd.DataFrame()

def _processar_campos_dataframe(df):
    """
    Processa campos específicos do DataFrame
    
    Args:
        df: DataFrame com os dados brutos
        
    Returns:
        DataFrame processado
    """
    # Converter tipos de dados
    if 'ID' in df.columns:
        df['ID'] = df['ID'].astype(str)
    
    if 'ASSIGNED_BY_ID' in df.columns:
        df['ASSIGNED_BY_ID'] = df['ASSIGNED_BY_ID'].astype(str)
    
    if 'TITLE' in df.columns:
        df['TITLE'] = df['TITLE'].astype(str)
    
    # Tratar campos específicos
    if 'DATE_CREATE' in df.columns:
        df['CREATED_DATE'] = pd.to_datetime(df['DATE_CREATE'], errors='coerce')
    else:
        # Criar uma coluna de data de criação padrão se não existir
        df['CREATED_DATE'] = pd.Timestamp.now()
        print("INFO: Coluna DATE_CREATE não encontrada nos dados. Usando data atual como padrão.")
    
    if 'DATE_MODIFY' in df.columns:
        df['UPDATE_DATE'] = pd.to_datetime(df['DATE_MODIFY'], errors='coerce')
    else:
        # Criar uma coluna de data de atualização padrão se não existir
        df['UPDATE_DATE'] = pd.Timestamp.now()
    
    # Processar os campos personalizados de higienização
    for nome_campo, campo_uf in CAMPOS_PERSONALIZADOS.items():
        # Ignorar o campo de status geral
        if nome_campo == "STATUS_HIGILIZACAO":
            continue
            
        # Verificar se o campo existe no DataFrame
        if campo_uf in df.columns:
            # Criar coluna de status: 1 se for "Sim" ou similar, 0 caso contrário (incluindo "Não", "nao" e valores vazios)
            coluna_status = f"{nome_campo}_STATUS"
            df[coluna_status] = df[campo_uf].apply(
                lambda x: 1 if pd.notna(x) and str(x).strip().lower() in ["sim", "s", "yes", "y", "true", "1"] else 0
            )
        else:
            # Se o campo não existir, criar coluna com valor padrão 0
            print(f"AVISO: Campo {campo_uf} não encontrado nos dados. Criando coluna de status vazia.")
            df[f"{nome_campo}_STATUS"] = 0
    
    # 2. Categorizar o status de higienização
    campo_status = CAMPOS_PERSONALIZADOS["STATUS_HIGILIZACAO"]
    if campo_status in df.columns:
        # Usar diretamente o valor do campo UF_CRM_HIGILIZACAO_STATUS sem categorização
        df["STATUS_CATEGORIA"] = df[campo_status]
    else:
        # Se o campo não existir, usar o mapeamento padrão de estágios
        if 'STAGE_ID' in df.columns:
            df['STATUS_CATEGORIA'] = df['STAGE_ID'].apply(lambda x: _categorizar_status(x))
        else:
            # Valor padrão se nenhum dos campos estiver disponível
            df['STATUS_CATEGORIA'] = "PENDENCIA"
            print("AVISO: Nenhum campo de status encontrado. Usando 'PENDENCIA' como valor padrão.")
    
    # Calcular pendências (exemplo - adaptar conforme necessário)
    pendencias = []
    for campo in ['TITLE', 'COMMENTS', 'PHONE', 'EMAIL']:
        if campo in df.columns:
            coluna = f'PENDENCIA_{campo}'
            df[coluna] = df[campo].isna() | (df[campo] == '')
            pendencias.append(coluna)
    
    # Calcular total de pendências
    if pendencias:
        df['TOTAL_PENDENCIAS'] = df[pendencias].sum(axis=1)
    else:
        df['TOTAL_PENDENCIAS'] = 0
    
    # Exibir informações sobre as colunas disponíveis para debug
    print(f"INFO: Colunas disponíveis após processamento: {df.columns.tolist()}")
    
    return df

def _categorizar_status(valor):
    """
    Categoriza o status de um negócio com base no estágio
    
    Args:
        valor: Valor do estágio
        
    Returns:
        Categoria de status (PENDENTE, EM_ANDAMENTO, COMPLETO, CANCELADO, OUTRO)
    """
    # Estágios de negócio pendentes
    if valor in ["C32:NEW", "C32:PREPARATION"]:
        return "PENDENTE"
    
    # Estágios de negócio em andamento
    elif valor in ["C32:EXECUTING", "C32:FINAL_INVOICE"]:
        return "EM_ANDAMENTO"
    
    # Estágios de negócio completos
    elif valor in ["C32:WON", "C32:FINAL_INVOICE_WON"]:
        return "COMPLETO"
    
    # Estágios de negócio cancelados
    elif valor in ["C32:LOSE"]:
        return "CANCELADO"
    
    # Outros estágios
    else:
        return "OUTRO"

# Executar a aplicação
if __name__ == "__main__":
    main() 
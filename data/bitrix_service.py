"""Serviço para gerenciar dados do Bitrix24"""
import pandas as pd
import streamlit as st
import requests
import time
from typing import Optional, Dict, Any, Tuple, List, Union
from config.settings import CATEGORY_ID, CAMPOS_PERSONALIZADOS

class BitrixService:
    """Classe para interagir com a API do Bitrix24"""
    
    # Dados de conexão com o Bitrix24
    BITRIX_BASE_URL = "https://eunaeuropacidadania.bitrix24.com.br/bitrix/tools/biconnector/pbi.php"
    BITRIX_TOKEN = "RuUSETRkbFD3whitfgMbioX8qjLgcdPubr"
    
    def consultar_bitrix(self, table, params=None, filtros=None, fields=None, max_registros=None) -> List[Dict]:
        """
        Consulta a API do Bitrix24 e retorna os dados
        
        Args:
            table: Nome da tabela a ser consultada
            params: Parâmetros adicionais para a consulta na URL (opcional)
            filtros: Filtros no formato JSON para o corpo da requisição (opcional)
            fields: Campos a serem retornados (opcional)
            max_registros: Número máximo de registros a serem retornados (opcional)
            
        Returns:
            Lista de dicionários com os dados
        """
        # Inicializa debug_info
        debug_info = {
            "timestamp": pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S'),
            "table": table,
            "params": params,
            "filtros": filtros,
            "sucesso": False,
            "mensagem": "",
            "detalhes": {}
        }
        
        # Verifica se o token está configurado
        if not self.BITRIX_TOKEN:
            debug_info["mensagem"] = "Token do Bitrix24 não configurado"
            if 'bitrix_debug' in st.session_state:
                st.session_state['bitrix_debug'].append(debug_info)
            return []
        
        # Constrói a URL
        url = f"{self.BITRIX_BASE_URL}?token={self.BITRIX_TOKEN}&table={table}"
        
        # Adiciona os parâmetros à URL
        if params:
            for key, value in params.items():
                url += f"&{key}={value}"
                
        # Adiciona os campos à URL
        if fields:
            fields_str = ",".join(fields)
            url += f"&fields={fields_str}"
            
        # Adiciona o limite à URL
        if max_registros:
            url += f"&limit={max_registros}"
            
        debug_info["url"] = url
        
        # Consulta a API
        try:
            # Usar POST com filtros no corpo se houver filtros definidos
            if filtros:
                response = requests.post(url, json=filtros, timeout=30)
                debug_info["metodo"] = "POST"
            else:
                response = requests.get(url, timeout=30)
                debug_info["metodo"] = "GET"
                
            debug_info["status_code"] = response.status_code
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    debug_info["tipo_resposta"] = type(data).__name__
                    debug_info["detalhes"]["formato"] = "lista" if isinstance(data, list) else "dicionário" if isinstance(data, dict) else "outro"
                    
                    # Caso 1: Resposta em formato de lista (formato tradicional)
                    if isinstance(data, list):
                        if len(data) > 0:
                            debug_info["sucesso"] = True
                            debug_info["mensagem"] = "Consulta bem-sucedida (formato: lista)"
                            debug_info["registros"] = len(data) - 1 if len(data) > 1 else 0
                        else:
                            debug_info["mensagem"] = "Resposta válida, mas lista vazia"
                        result = data
                    
                    # Caso 2: Resposta em formato de dicionário (novo formato da API)
                    elif isinstance(data, dict):
                        # Verificar se é uma resposta de erro da API
                        if 'error' in data:
                            debug_info["mensagem"] = f"Erro na API: {data.get('error_description', data['error'])}"
                            debug_info["detalhes"]["erro_api"] = data
                            result = []
                        # Verificar se contém o resultado no formato esperado para conversão
                        elif 'result' in data and isinstance(data['result'], dict):
                            result_data = data['result']
                            
                            # Verificar o formato específico com fields e items
                            if 'fields' in result_data and 'items' in result_data:
                                fields = result_data['fields']
                                items = result_data['items']
                                
                                # Converter para o formato de lista esperado
                                converted_data = [fields]  # Primeira linha são os campos
                                
                                # Adicionar os itens
                                for item_id, item_values in items.items():
                                    item_dict = {'ID': item_id}
                                    item_dict.update(item_values)
                                    converted_data.append(item_dict)
                                
                                debug_info["sucesso"] = True
                                debug_info["mensagem"] = "Consulta bem-sucedida (formato: dicionário convertido)"
                                debug_info["registros"] = len(items)
                                debug_info["detalhes"]["colunas"] = fields
                                result = converted_data
                            else:
                                debug_info["mensagem"] = "Resposta em formato de dicionário, mas estrutura incompatível"
                                debug_info["detalhes"]["estrutura"] = list(result_data.keys())
                                result = []
                        else:
                            debug_info["mensagem"] = "Formato de dicionário desconhecido"
                            debug_info["detalhes"]["chaves"] = list(data.keys())
                            result = []
                    
                    # Caso 3: Formato desconhecido
                    else:
                        debug_info["mensagem"] = f"Formato de resposta desconhecido: {type(data).__name__}"
                        result = []
                
                except ValueError as e:
                    debug_info["mensagem"] = f"Erro ao processar JSON: {str(e)}"
                    debug_info["detalhes"]["conteudo_parcial"] = response.text[:200] + "..." if len(response.text) > 200 else response.text
                    result = []
            else:
                debug_info["mensagem"] = f"Erro HTTP: {response.status_code}"
                if response.status_code in [401, 403]:
                    debug_info["detalhes"]["causa"] = "Erro de autenticação. Verifique o token."
                elif response.status_code == 404:
                    debug_info["detalhes"]["causa"] = "Recurso não encontrado. Verifique a URL."
                result = []
                
        except requests.exceptions.RequestException as e:
            debug_info["mensagem"] = f"Erro de conexão: {str(e)}"
            result = []
            
        # Armazena as informações de debug
        if 'bitrix_debug' in st.session_state:
            st.session_state['bitrix_debug'].append(debug_info)
            
        return result
    
    @st.cache_data(ttl=300)
    def obter_dados_higienizacao(self, category_id=None, max_retries=3):
        """
        Obtém dados de negócios para o dashboard de higienização
        
        Args:
            category_id: ID da categoria a ser consultada (opcional)
            max_retries: Número máximo de tentativas
            
        Returns:
            Tuple (DataFrame, dict): DataFrame com os dados e dicionário de métricas
        """
        # Usar o ID da categoria das configurações se não for especificado
        if category_id is None:
            category_id = CATEGORY_ID
            
        # Parâmetros da consulta
        params = {
            "filter[CATEGORY_ID]": category_id
        }
        
        # Consultar a API
        dados = self.consultar_bitrix("crm.deal.list", params=params, max_registros=500)
        
        # Verificar se há dados suficientes para processar
        if not dados or len(dados) <= 1:
            st.error("Não foram encontrados dados para processar")
            return None
            
        # Extrair cabeçalho e dados
        headers = dados[0]
        rows = dados[1:]
        
        # Criar DataFrame
        df = pd.DataFrame(rows, columns=headers)
        
        # Processar dados
        try:
            # Converter datas
            if 'DATE_CREATE' in df.columns:
                df['DATA_CRIACAO'] = pd.to_datetime(df['DATE_CREATE'], errors='coerce')
                
            if 'DATE_MODIFY' in df.columns:
                df['DATA_MODIFICACAO'] = pd.to_datetime(df['DATE_MODIFY'], errors='coerce')
            
            # Categorizar status
            if 'STAGE_ID' in df.columns:
                df['STATUS_CATEGORIA'] = df['STAGE_ID'].apply(self._categorizar_status)
            
            # Colunas de pendências
            campos_obrigatorios = ['TITLE', 'COMPANY_ID', 'CONTACT_ID']
            for campo in campos_obrigatorios:
                if campo in df.columns:
                    # Verificar se o campo está vazio ou nulo
                    df[f'PENDENCIA_{campo}'] = df[campo].isnull() | (df[campo] == '')
            
            # Total de pendências
            colunas_pendencia = [col for col in df.columns if col.startswith('PENDENCIA_')]
            df['TOTAL_PENDENCIAS'] = df[colunas_pendencia].sum(axis=1)
            
            # Calcular métricas
            metricas = self._calcular_metricas(df)
            
            return df, metricas
            
        except Exception as e:
            st.error(f"Erro ao processar dados: {str(e)}")
            return None
    
    def _categorizar_status(self, stage_id):
        """
        Categoriza o status com base no ID do estágio
        
        Args:
            stage_id: ID do estágio no Bitrix24
            
        Returns:
            Status categorizado
        """
        # Adaptar conforme necessário de acordo com seus estágios no Bitrix24
        if stage_id in ['C1:NEW', 'C1:PREPARATION']:
            return "PENDENTE"
        elif stage_id in ['C1:EXECUTING']:
            return "EM_ANDAMENTO"
        elif stage_id in ['C1:FINAL_INVOICE', 'C1:WON']:
            return "COMPLETO"
        elif stage_id in ['C1:LOSE']:
            return "CANCELADO"
        else:
            return "OUTRO"
    
    def _calcular_metricas(self, df):
        """
        Calcula métricas para o dashboard
        
        Args:
            df: DataFrame com os dados
            
        Returns:
            Dicionário com as métricas
        """
        # Total de registros
        total_registros = len(df)
        
        # Contagem por status
        status_counts = df['STATUS_CATEGORIA'].value_counts()
        
        # Total de completos
        completos = status_counts.get('COMPLETO', 0)
        
        # Percentual de concluídos
        percentual_concluido = (completos / total_registros * 100) if total_registros > 0 else 0
        
        # Total de pendências
        total_pendencias = df['TOTAL_PENDENCIAS'].sum()
        
        # Criar dicionário de métricas
        metricas = {
            "total_registros": total_registros,
            "completos": completos,
            "pendentes": status_counts.get('PENDENTE', 0),
            "em_andamento": status_counts.get('EM_ANDAMENTO', 0),
            "cancelados": status_counts.get('CANCELADO', 0),
            "percentual_concluido": percentual_concluido,
            "total_pendencias": total_pendencias
        }
        
        return metricas
    
    def clear_cache(self):
        """Limpa o cache do serviço"""
        st.cache_data.clear()
        
    def testar_conexao(self) -> Dict[str, Any]:
        """
        Testa a conexão com o Bitrix24
        
        Returns:
            Dicionário com informações sobre o teste de conexão
        """
        # Reset dos logs de debug
        if 'bitrix_debug' in st.session_state:
            st.session_state['bitrix_debug'] = []
            
        resultado = {
            "timestamp": pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S'),
            "sucesso": False,
            "mensagem": "",
            "detalhes": {}
        }
        
        try:
            # Teste de conexão básica com limite de 1 registro
            url_teste = f"{self.BITRIX_BASE_URL}?token={self.BITRIX_TOKEN}&table=crm_deal&limit=1"
            
            # Filtro básico para testar
            filtro_teste = {
                "dimensionsFilters": [[
                    {
                        "fieldName": "ID",
                        "type": "INCLUDE",
                        "operator": "NOT_NULL"
                    }
                ]]
            }
            
            # Tentar conectar usando POST com filtro
            response = requests.post(url_teste, json=filtro_teste, timeout=10)
            
            # Verificar status da resposta
            resultado["detalhes"]["status_code"] = response.status_code
            resultado["detalhes"]["metodo"] = "POST"
            resultado["detalhes"]["url"] = url_teste
            
            if response.status_code == 200:
                # Verificar se o conteúdo é JSON válido
                try:
                    data = response.json()
                    resultado["detalhes"]["tipo_resposta"] = type(data).__name__
                    resultado["detalhes"]["formato_resposta"] = "lista" if isinstance(data, list) else "dicionário" if isinstance(data, dict) else "outro"
                    
                    # Informações específicas para cada formato
                    if isinstance(data, list):
                        resultado["detalhes"]["tamanho_lista"] = len(data)
                        if len(data) > 0:
                            resultado["sucesso"] = True
                            resultado["mensagem"] = "Conexão bem-sucedida (formato: lista)"
                            if len(data) > 1:
                                resultado["detalhes"]["colunas"] = data[0]
                                resultado["detalhes"]["num_registros"] = len(data) - 1
                            else:
                                resultado["detalhes"]["conteudo"] = data[0]
                        else:
                            resultado["mensagem"] = "Resposta é uma lista vazia"
                    elif isinstance(data, dict):
                        resultado["detalhes"]["chaves"] = list(data.keys())
                        
                        # Verificar se é uma resposta de erro
                        if 'error' in data:
                            resultado["mensagem"] = f"Erro na API: {data.get('error_description', data['error'])}"
                            resultado["detalhes"]["erro_api"] = data
                        # Verificar se tem o formato esperado para conversão
                        elif 'result' in data and isinstance(data['result'], dict):
                            result = data['result']
                            if 'fields' in result and 'items' in result:
                                resultado["sucesso"] = True
                                resultado["mensagem"] = "Conexão bem-sucedida (formato: dicionário convertível)"
                                resultado["detalhes"]["num_campos"] = len(result.get('fields', []))
                                resultado["detalhes"]["num_registros"] = len(result.get('items', []))
                            else:
                                resultado["mensagem"] = "Resposta em formato de dicionário, mas estrutura incompatível"
                        else:
                            resultado["mensagem"] = "Resposta em formato de dicionário sem estrutura esperada"
                            resultado["detalhes"]["amostra"] = str(data)[:500] + "..." if len(str(data)) > 500 else str(data)
                    else:
                        resultado["mensagem"] = f"Resposta em formato desconhecido: {type(data).__name__}"
                except ValueError as e:
                    resultado["mensagem"] = f"Resposta não é um JSON válido: {str(e)}"
                    resultado["detalhes"]["conteudo_parcial"] = response.text[:200] + "..." if len(response.text) > 200 else response.text
            elif response.status_code == 401 or response.status_code == 403:
                resultado["mensagem"] = "Erro de autenticação. Verifique o token."
            elif response.status_code == 404:
                resultado["mensagem"] = "Recurso não encontrado. Verifique a URL."
            else:
                resultado["mensagem"] = f"Erro HTTP: {response.status_code}"
                
        except requests.exceptions.Timeout:
            resultado["mensagem"] = "Timeout. O servidor demorou muito para responder."
        except requests.exceptions.ConnectionError:
            resultado["mensagem"] = "Erro de conexão. Verifique sua internet."
        except Exception as e:
            resultado["mensagem"] = f"Erro inesperado: {str(e)}"
            
        # Armazenar o resultado no histórico de debug
        if 'bitrix_debug' in st.session_state:
            st.session_state['bitrix_debug'].append(resultado)
            
        return resultado

# Instância global do serviço
bitrix_service = BitrixService() 
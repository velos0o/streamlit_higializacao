import streamlit as st
import pandas as pd
from api.bitrix_connector import load_bitrix_data, get_credentials
from datetime import datetime
from dotenv import load_dotenv
import os
import json
import re # Para remoção de pontuação e prefixos
from unidecode import unidecode # Para remover acentos

# Try importing thefuzz, provide guidance if not found
try:
    from thefuzz import process, fuzz
except ImportError:
    st.error("Biblioteca 'thefuzz' não encontrada. Por favor, instale com: pip install thefuzz python-Levenshtein")
    # You might want to stop execution or return an empty DataFrame here
    # For now, let functions proceed but fuzzy matching will fail if called.
    process = None
    fuzz = None

# Carregar variáveis de ambiente
load_dotenv()

def _limpar_antes_normalizar(series):
    """Tenta remover texto extra após vírgula, parêntese, barra ou hífen e prefixos natti/matri."""
    if not isinstance(series, pd.Series):
        series = pd.Series(series)
    
    # Remover prefixos natti/matri primeiro
    series = series.astype(str).str.lower()
    series = series.str.replace(r'^natti\s*[:-]?\s*', '', regex=True)
    series = series.str.replace(r'^matri\s*[:-]?\s*', '', regex=True)
    # Remover prefixos como "-natti..." ou "- matri..."
    series = series.str.replace(r'^-\s*natti\s*[:-]?\s*', '', regex=True)
    series = series.str.replace(r'^-\s*matri\s*[:-]?\s*', '', regex=True)

    def clean_text(text):
        if pd.isna(text) or not isinstance(text, str): return text
        # Tenta dividir por separadores e pegar a primeira parte
        separadores = [',', '(', '/', '-']
        for sep in separadores:
            if sep in text:
                text = text.split(sep, 1)[0]
        return text.strip()

    return series.apply(clean_text)

def _normalizar_localizacao(series):
    """Normalização agressiva para campos de localização."""
    if not isinstance(series, pd.Series):
        series = pd.Series(series)
        
    # 1. Converter para string e minúsculas (já feito parcialmente em _limpar_antes_normalizar)
    normalized = series.fillna('').astype(str).str.lower()
    
    # 2. Remover acentos
    try:
        normalized = normalized.apply(lambda x: unidecode(x) if isinstance(x, str) else x)
    except Exception:
         normalized = pd.Series([unidecode(str(x)) for x in series.fillna('')], index=series.index)
         normalized = normalized.str.lower()

    # 3. Remover prefixos GERAIS comuns
    prefixos_gerais = ['comune di ', 'provincia di ', 'parrocchia di ', 'parrocchia ', 'citta di ', 'diocese di ', 'chiesa di ', 'chiesa parrocchiale di ']
    for prefix in prefixos_gerais:
        normalized = normalized.str.replace(f'^{re.escape(prefix)}', '', regex=True)
        
    # 3.5 Remover prefixos RELIGIOSOS comuns (após os gerais)
    prefixos_religiosos = ['san ', 'santa ', 'santi ', 'santo ', 's ', 'ss '] # Adicionado 'ss '
    for prefix in prefixos_religiosos:
        # Usar word boundary (\b) para evitar remover 'san' de 'sanremo'
        normalized = normalized.str.replace(f'^{re.escape(prefix)}(\\b)?', '', regex=True)

    # 4. Remover pontuação básica
    normalized = normalized.str.replace(r'[\'"\.,;!?()[\]{}]', '', regex=True)

    # 4.5 Remover sufixos de província (espaço + 2 letras maiúsculas no fim)
    # Primeiro remove o padrão com espaço, depois o padrão entre parênteses (se houver)
    normalized = normalized.str.replace(r'\s+[a-z]{2}$', '', regex=True) # Remove ' xx' no final
    normalized = normalized.str.replace(r'\s*\([a-z]{2}\)$', '', regex=True) # Remove ' (xx)' no final
    normalized = normalized.str.strip() # Garante remoção de espaços caso o sufixo fosse a única coisa após a limpeza

    # 5. Remover espaços extras
    normalized = normalized.str.strip()
    normalized = normalized.str.replace(r'\s+', ' ', regex=True)
    
    # 6. Tratar valores que se tornaram vazios após limpeza ou eram nulos originalmente
    normalized = normalized.replace(['', 'nan', 'none', 'null'], 'nao especificado', regex=False)
    
    return normalized

def carregar_datas_solicitacao():
    """
    Carrega as datas de solicitação originais do arquivo CSV.
    """
    # Construir o caminho relativo para o arquivo CSV
    script_dir = os.path.dirname(__file__) # Diretório atual do script
    csv_path = os.path.join(script_dir, 'Planilhas', 'Emissões Italiana, Antes de movimentação geral - comune.csv')

    try:
        df_datas = pd.read_csv(csv_path, usecols=['ID', 'Movido em'], dtype={'ID': str})
        # Renomear colunas
        df_datas = df_datas.rename(columns={'Movido em': 'DATA_SOLICITACAO_ORIGINAL'})
        # Converter para datetime, tratando erros
        df_datas['DATA_SOLICITACAO_ORIGINAL'] = pd.to_datetime(df_datas['DATA_SOLICITACAO_ORIGINAL'], errors='coerce')
        # Remover linhas onde a data não pôde ser convertida ou o ID é nulo
        df_datas.dropna(subset=['ID', 'DATA_SOLICITACAO_ORIGINAL'], inplace=True)
        # Remover IDs duplicados, mantendo o primeiro (ou último, dependendo da lógica desejada)
        df_datas.drop_duplicates(subset=['ID'], keep='first', inplace=True)
        return df_datas
    except FileNotFoundError:
        st.error(f"Arquivo CSV não encontrado em: {csv_path}")
        return pd.DataFrame({'ID': [], 'DATA_SOLICITACAO_ORIGINAL': []})
    except Exception as e:
        st.error(f"Erro ao ler o arquivo CSV: {e}")
        return pd.DataFrame({'ID': [], 'DATA_SOLICITACAO_ORIGINAL': []})

def carregar_coordenadas_mapa():
    """
    Carrega as coordenadas do arquivo JSON mapa_italia.json e normaliza.
    """
    script_dir = os.path.dirname(__file__)
    json_path = os.path.join(script_dir, 'Mapa', 'mapa_italia.json')
    
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data_json = json.load(f)
        df_coords = pd.DataFrame(data_json)
        
        cols_necessarias = ['city', 'admin_name', 'lat', 'lng']
        if not all(col in df_coords.columns for col in cols_necessarias):
            cols_faltantes = [col for col in cols_necessarias if col not in df_coords.columns]
            st.error(f"JSON {json_path} sem colunas: {cols_faltantes}. Necessário: {cols_necessarias}")
            return pd.DataFrame()
        
        df_coords = df_coords[cols_necessarias].copy()
        df_coords = df_coords.rename(columns={
            'city': 'COMUNE_MAPA_ORIG', 
            'admin_name': 'PROVINCIA_MAPA_ORIG',
            'lat': 'latitude',
            'lng': 'longitude'
        })
        
        # Aplicar Normalização Agressiva
        df_coords['COMUNE_MAPA_NORM'] = _normalizar_localizacao(df_coords['COMUNE_MAPA_ORIG'])
        df_coords['PROVINCIA_MAPA_NORM'] = _normalizar_localizacao(df_coords['PROVINCIA_MAPA_ORIG'])
        
        # Remover duplicatas baseadas nas colunas normalizadas
        # Mantém a primeira ocorrência de uma combinação (Comune, Provincia)
        df_coords.drop_duplicates(subset=['COMUNE_MAPA_NORM', 'PROVINCIA_MAPA_NORM'], keep='first', inplace=True)
        # Opcional: Remover duplicatas baseadas APENAS no comune (se quiser apenas uma coord por comune)
        # df_coords.drop_duplicates(subset=['COMUNE_MAPA_NORM'], keep='first', inplace=True)
        
        df_coords_final = df_coords[['COMUNE_MAPA_NORM', 'PROVINCIA_MAPA_NORM', 'latitude', 'longitude']].copy()

        df_coords_final['latitude'] = pd.to_numeric(df_coords_final['latitude'], errors='coerce')
        df_coords_final['longitude'] = pd.to_numeric(df_coords_final['longitude'], errors='coerce')
        df_coords_final.dropna(subset=['latitude', 'longitude'], inplace=True)

        print(f"Carregadas {len(df_coords_final)} coordenadas únicas (Comune+Prov) e válidas do JSON.")
        return df_coords_final
        
    except FileNotFoundError:
        st.error(f"Arquivo JSON de coordenadas não encontrado em: {json_path}")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Erro ao ler ou processar o arquivo JSON de coordenadas: {e}")
        return pd.DataFrame()

def carregar_dados_comune():
    """
    Carrega dados do Bitrix, normaliza locais (com limpeza prévia), 
    junta datas e coordenadas (APENAS fuzzy matching no Comune).
    """
    # --- Carregar Bitrix --- 
    BITRIX_TOKEN, BITRIX_URL = get_credentials()
    url_items = f"{BITRIX_URL}/bitrix/tools/biconnector/pbi.php?token={BITRIX_TOKEN}&table=crm_dynamic_items_1052"
    category_filter = {"dimensionsFilters": [[{
        "fieldName": "CATEGORY_ID", "values": ["22"], "type": "INCLUDE", "operator": "EQUALS"
    }]]}
    df_items = load_bitrix_data(url_items, filters=category_filter)
    if df_items is None or df_items.empty: return pd.DataFrame()
    if 'ID' not in df_items.columns: return pd.DataFrame()
    df_items['ID'] = df_items['ID'].astype(str)

    # --- Normalizar Locais Bitrix (com limpeza prévia do Comune) --- 
    col_provincia_bitrix = 'UF_CRM_12_1743015702671'
    col_comune_bitrix = 'UF_CRM_12_1722881735827'

    if col_provincia_bitrix in df_items.columns:
        df_items['PROVINCIA_ORIG'] = df_items[col_provincia_bitrix]
        # Normalizar província (pode não ser usada para merge, mas útil para exibição)
        df_items['PROVINCIA_NORM'] = _normalizar_localizacao(df_items[col_provincia_bitrix])
    else:
        df_items['PROVINCIA_ORIG'] = 'Não Especificado'; df_items['PROVINCIA_NORM'] = 'nao especificado'

    if col_comune_bitrix in df_items.columns:
        df_items['COMUNE_ORIG'] = df_items[col_comune_bitrix]
        # 1. Limpar antes de normalizar
        comunes_limpos = _limpar_antes_normalizar(df_items[col_comune_bitrix])
        # 2. Normalizar o resultado limpo
        df_items['COMUNE_NORM'] = _normalizar_localizacao(comunes_limpos)
    else:
        df_items['COMUNE_ORIG'] = 'Não Especificado'; df_items['COMUNE_NORM'] = 'nao especificado'
        
    # --- Imprimir Diagnóstico (opcional, pode comentar após análise) --- 
    # try:
    #     bitrix_unique_pairs = df_items[['PROVINCIA_NORM', 'COMUNE_NORM']].drop_duplicates().sort_values(by=['PROVINCIA_NORM', 'COMUNE_NORM']).values.tolist()
    #     print("\n--- Nomes Únicos Normalizados no Bitrix (Após Limpeza Prévia) ---")
    #     # ... (código de impressão) ...
    # except Exception as e:
    #     print(f"Erro diagnóstico Bitrix: {e}")
    # ----

    # --- Juntar Datas CSV --- 
    df_datas_solicitacao = carregar_datas_solicitacao()
    if not df_datas_solicitacao.empty:
        df_items = pd.merge(df_items, df_datas_solicitacao, on='ID', how='left')
        print(f"{df_items['DATA_SOLICITACAO_ORIGINAL'].notna().sum()}/{len(df_items)} registros com data.")
    else: df_items['DATA_SOLICITACAO_ORIGINAL'] = pd.NaT
    
    # --- Juntar Coordenadas (JSON) - APENAS Fuzzy no Comune --- 
    df_coordenadas = carregar_coordenadas_mapa()
    
    df_items['latitude'] = pd.NA
    df_items['longitude'] = pd.NA
    df_items['COORD_SOURCE'] = pd.NA

    if not df_coordenadas.empty and process is not None and fuzz is not None:
        print("\nIniciando busca de coordenadas via Fuzzy Match (Comune Only)...")
        # Lista de nomes de comunes únicos do JSON para comparar
        json_comunes_norm_list = df_coordenadas['COMUNE_MAPA_NORM'].unique().tolist()
        if 'nao especificado' in json_comunes_norm_list: 
            json_comunes_norm_list.remove('nao especificado')

        if json_comunes_norm_list:
            # Nomes únicos de comunes do Bitrix 
            bitrix_comunes_to_match = df_items['COMUNE_NORM'].unique().tolist()
            
            fuzzy_matches_map = {}
            match_threshold = 90 # Limite de similaridade
            
            print(f"Realizando fuzzy matching para {len(bitrix_comunes_to_match)} comunes únicos do Bitrix...")
            matched_count_fuzzy = 0
            for bitrix_comune in bitrix_comunes_to_match:
                if bitrix_comune == 'nao especificado': continue 
                
                best_match = process.extractOne(
                    query=bitrix_comune,
                    choices=json_comunes_norm_list,
                    scorer=fuzz.token_sort_ratio, 
                    score_cutoff=match_threshold
                )
                
                if best_match:
                    fuzzy_matches_map[bitrix_comune] = best_match[0] 
                    matched_count_fuzzy += 1

            print(f"Fuzzy matching concluído. Encontrados {matched_count_fuzzy} mapeamentos potenciais acima de {match_threshold}%.")

            if fuzzy_matches_map:
                df_items['JSON_COMUNE_FUZZY_MATCH'] = df_items['COMUNE_NORM'].map(fuzzy_matches_map)

                # Preparar coordenadas únicas por comune JSON para o merge
                coords_c_fuzzy = df_coordenadas[['COMUNE_MAPA_NORM', 'latitude', 'longitude']]
                coords_c_fuzzy = coords_c_fuzzy.drop_duplicates(subset=['COMUNE_MAPA_NORM'], keep='first')
                coords_c_fuzzy = coords_c_fuzzy.rename(columns={'latitude':'lat_fuzzy', 'longitude':'lon_fuzzy'})
                
                # Fazer merge com base no nome do comune JSON mapeado
                df_items = pd.merge(
                    df_items, 
                    coords_c_fuzzy, 
                    left_on='JSON_COMUNE_FUZZY_MATCH', 
                    right_on='COMUNE_MAPA_NORM', 
                    how='left',
                    suffixes=('', '_fuzzy')
                )

                # Preencher coordenadas onde houve match fuzzy
                mask_fuzzy_update = df_items['lat_fuzzy'].notna()
                # Sobrescrever latitude/longitude NA com os valores do fuzzy match
                df_items.loc[mask_fuzzy_update, 'latitude'] = df_items.loc[mask_fuzzy_update, 'lat_fuzzy']
                df_items.loc[mask_fuzzy_update, 'longitude'] = df_items.loc[mask_fuzzy_update, 'lon_fuzzy']
                df_items.loc[mask_fuzzy_update, 'COORD_SOURCE'] = 'FuzzyMatch_Comune'
                count_fuzzy_applied = mask_fuzzy_update.sum()
                print(f"{count_fuzzy_applied} correspondências aplicadas (Fuzzy Comune Only).")
                
                # Limpar colunas temporárias
                df_items.drop(columns=['JSON_COMUNE_FUZZY_MATCH', 'COMUNE_MAPA_NORM', 'lat_fuzzy', 'lon_fuzzy'], inplace=True, errors='ignore')
        else:
            print("Não há nomes de comunes válidos no arquivo JSON para realizar o fuzzy matching.")
    elif not df_coordenadas.empty:
         print("Fuzzy matching não executado pois a biblioteca 'thefuzz' não foi importada.")
         st.warning("Instale 'thefuzz' e 'python-Levenshtein' para habilitar o fuzzy matching.")
    else:
        print("Arquivo de coordenadas vazio ou não carregado. Nenhuma coordenada adicionada.")
        
    # --- Finalização --- 
    df_items.loc[:, 'NOME_SEGMENTO'] = "COMUNE BITRIX24"
    return df_items

def carregar_dados_negocios():
    """
    Carrega os dados dos negócios da categoria 32 e seus campos personalizados
    
    Returns:
        tuple: (DataFrame com negócios, DataFrame com campos personalizados)
    """
    # Obter token do Bitrix24
    BITRIX_TOKEN, BITRIX_URL = get_credentials()
    
    # URLs para acessar as tabelas
    url_deal = f"{BITRIX_URL}/bitrix/tools/biconnector/pbi.php?token={BITRIX_TOKEN}&table=crm_deal"
    url_deal_uf = f"{BITRIX_URL}/bitrix/tools/biconnector/pbi.php?token={BITRIX_TOKEN}&table=crm_deal_uf"
    
    # Preparar filtro para a categoria 32
    category_filter = {"dimensionsFilters": [[]]}
    category_filter["dimensionsFilters"][0].append({
        "fieldName": "CATEGORY_ID", 
        "values": ["32"], 
        "type": "INCLUDE", 
        "operator": "EQUALS"
    })
    
    # Log do filtro aplicado
    print(f"Aplicando filtro para CRM_DEAL: {category_filter}")
    
    # Carregar dados principais dos negócios com filtro de categoria
    df_deal = load_bitrix_data(url_deal, filters=category_filter)
    
    # Verificar se conseguiu carregar os dados
    if df_deal.empty:
        print("Nenhum dado encontrado para CRM_DEAL com CATEGORY_ID=32")
        return pd.DataFrame(), pd.DataFrame()
    else:
        print(f"Carregados {len(df_deal)} registros de CRM_DEAL com CATEGORY_ID=32")
        
    # Verificar se a coluna CATEGORY_ID existe e tem valores esperados
    if 'CATEGORY_ID' in df_deal.columns:
        categorias_encontradas = df_deal['CATEGORY_ID'].unique()
        print(f"Categorias encontradas nos dados: {categorias_encontradas}")
    
    # Simplificar: selecionar apenas as colunas necessárias
    colunas_deal = ['ID', 'TITLE', 'ASSIGNED_BY_NAME']
    
    # Verificar se todas as colunas existem
    colunas_existentes = [col for col in colunas_deal if col in df_deal.columns]
    if len(colunas_existentes) < len(colunas_deal):
        print(f"Aviso: Nem todas as colunas desejadas existem. Colunas disponíveis: {df_deal.columns.tolist()}")
    
    # Selecionar apenas as colunas que existem
    df_deal = df_deal[colunas_existentes]
    
    # Obter lista de IDs dos deals para filtrar a tabela crm_deal_uf
    deal_ids = df_deal['ID'].astype(str).tolist()
    
    # Mostrar alguns IDs para debug
    print(f"Exemplos de IDs de deals que serão usados: {deal_ids[:5] if len(deal_ids) > 5 else deal_ids}")
    
    # Limitar a quantidade de IDs para evitar sobrecarga (se houverem muitos)
    if len(deal_ids) > 1000:
        print(f"Limitando a consulta para os primeiros 1000 IDs (de {len(deal_ids)} disponíveis)")
        deal_ids = deal_ids[:1000]
    
    # Se não houver IDs, retornar DataFrames vazios
    if not deal_ids:
        print("Nenhum ID de deal encontrado para filtrar campos personalizados")
        return df_deal, pd.DataFrame()
    
    # Filtro para crm_deal_uf baseado nos IDs dos deals da categoria 32
    deal_filter = {"dimensionsFilters": [[]]}
    deal_filter["dimensionsFilters"][0].append({
        "fieldName": "DEAL_ID", 
        "values": deal_ids, 
        "type": "INCLUDE", 
        "operator": "EQUALS"
    })
    
    print(f"Aplicando filtro para CRM_DEAL_UF com {len(deal_ids)} IDs")
    
    # Carregar dados da tabela crm_deal_uf (onde estão os campos personalizados do funil de negócios)
    df_deal_uf = load_bitrix_data(url_deal_uf, filters=deal_filter)
    
    # Verificar se conseguiu carregar os dados
    if df_deal_uf.empty:
        print("Nenhum dado encontrado em DEAL_UF para os IDs filtrados")
        return df_deal, pd.DataFrame()
    else:
        print(f"Carregados {len(df_deal_uf)} registros de DEAL_UF")
    
    # Verificar as colunas disponíveis em df_deal_uf
    print(f"Colunas disponíveis em DEAL_UF: {df_deal_uf.columns.tolist()}")
    
    # Filtrar apenas as colunas relevantes
    colunas_obrigatorias = ['DEAL_ID', 'UF_CRM_1722605592778']
    
    # Verificar quais colunas existem no DataFrame
    colunas_selecionadas = [coluna for coluna in colunas_obrigatorias if coluna in df_deal_uf.columns]
    
    if len(colunas_selecionadas) < len(colunas_obrigatorias):
        print(f"Aviso: Nem todas as colunas necessárias foram encontradas em DEAL_UF")
        print(f"Colunas necessárias: {colunas_obrigatorias}")
        print(f"Colunas encontradas: {colunas_selecionadas}")
    
    # Verificar se a coluna de cruzamento existe
    if 'UF_CRM_1722605592778' not in df_deal_uf.columns:
        print("ATENÇÃO: Coluna UF_CRM_1722605592778 não encontrada em DEAL_UF!")
        # Tentar sugerir colunas que possam conter o valor desejado
        possiveis_colunas = [col for col in df_deal_uf.columns if 'UF_CRM_' in col]
        if possiveis_colunas:
            print(f"Possíveis colunas alternativas: {possiveis_colunas}")
    
    # Simplificar: manter apenas as colunas necessárias
    if colunas_selecionadas:
        df_deal_uf = df_deal_uf[colunas_selecionadas]
    
    return df_deal, df_deal_uf

def carregar_estagios_bitrix():
    """
    Carrega os estágios dos funis do Bitrix24
    
    Returns:
        pandas.DataFrame: DataFrame com os estágios
    """
    # Obter token e URL do Bitrix24
    BITRIX_TOKEN, BITRIX_URL = get_credentials()
    
    # Obter estágios únicos do pipeline
    url_stages = f"{BITRIX_URL}/bitrix/tools/biconnector/pbi.php?token={BITRIX_TOKEN}&table=crm_status"
    df_stages = load_bitrix_data(url_stages)
    
    return df_stages

def mapear_estagios_comune():
    """
    Retorna um dicionário com mapeamento dos estágios do COMUNE
    """
    return {
        "DT1052_22:UC_2QZ8S2": "PENDENTE",
        "DT1052_22:UC_E1VKYT": "PESQUISA NÃO FINALIZADA",
        "DT1052_22:UC_MVS02R": "DEVOLUTIVA EMISSOR",
        "DT1052_22:NEW": "SOLICITAR",
        "DT1052_22:UC_4RQBZV": "URGENTE",
        "DT1052_22:UC_F0IRDH": "SOLICITAR - TEM INFO",
        "DT1052_22:PREPARATION": "AGUARDANDO COMUNE/PARÓQUIA",
        "DT1052_22:UC_S4DFU2": "AGUARDANDO COMUNE/PARÓQUIA - TEM INFO",
        "DT1052_22:UC_1RC076": "AGUARDANDO PDF",
        "DT1052_22:CLIENT": "ENTREGUE PDF",
        "DT1052_22:UC_A9UEMO": "NEGATIVA COMUNE",
        "DT1052_22:SUCCESS": "DOCUMENTO FISICO ENTREGUE",
        "DT1052_22:FAIL": "CANCELADO"
    }

def mapear_estagios_macro():
    """
    Retorna um dicionário com mapeamento dos estágios do COMUNE para a visão macro
    """
    return {
        "DT1052_22:UC_2QZ8S2": "PENDENTE",                    # PENDENTE
        "DT1052_22:UC_E1VKYT": "PESQUISA NÃO FINALIZADA",     # PESQUISA NÃO FINALIZADA
        "DT1052_22:UC_MVS02R": "DEVOLUTIVA EMISSOR",          # DEVOLUTIVA EMISSOR
        "DT1052_22:NEW": "SOLICITAR",                         # SOLICITAR
        "DT1052_22:UC_4RQBZV": "URGENTE",                     # URGENTE
        "DT1052_22:UC_F0IRDH": "SOLICITAR - TEM INFO",        # SOLICITAR - TEM INFO
        "DT1052_22:PREPARATION": "AGUARDANDO COMUNE/PARÓQUIA", # AGUARDANDO COMUNE/PARÓQUIA
        "DT1052_22:UC_S4DFU2": "AGUARDANDO COMUNE/PARÓQUIA - TEM INFO", # AGUARDANDO COMUNE/PARÓQUIA - TEM INFO
        "DT1052_22:UC_1RC076": "AGUARDANDO PDF",              # AGUARDANDO PDF
        "DT1052_22:CLIENT": "ENTREGUE PDF",                   # ENTREGUE PDF
        "DT1052_22:UC_A9UEMO": "NEGATIVA COMUNE",             # NEGATIVA COMUNE
        "DT1052_22:SUCCESS": "DOCUMENTO FISICO ENTREGUE",     # DOCUMENTO FISICO ENTREGUE
        "DT1052_22:FAIL": "CANCELADO"                         # CANCELADO
    } 
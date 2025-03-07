# Dashboard de Higialização

Dashboard desenvolvido em Streamlit para monitoramento e análise do processo de higialização de dados no Bitrix24. A aplicação permite acompanhar o status de registros, visualizar pendências e analisar a produtividade da equipe.

## Funcionalidades

- Acompanhamento de status de higialização por responsável
- Contagem de itens pendentes, incompletos e concluídos
- Tabela de pendências detalhada por categoria
- Tabela de produtividade mostrando itens concluídos por categoria
- Visualização de métricas de conversão
- Integração com Bitrix24 para obtenção de dados em tempo real
- Filtros por responsável, período e categoria
- Exportação de relatórios e dados processados

## Requisitos

- Python 3.8+
- Streamlit 1.32.0+
- Pandas 2.2.0+
- NumPy 1.26.3+
- Plotly 5.18.0+
- Requests 2.31.0+
- Python-dotenv 1.0.0+
- Streamlit-extras 0.3.6+
- Streamlit-option-menu 0.3.6+
- Streamlit-elements 0.1.0+

## Instalação

1. Clone o repositório:
```
git clone https://github.com/Velos0o/streamlit_higializacao.git
cd streamlit_higializacao
```

2. Instale as dependências:
```
pip install -r requirements.txt
```

3. Configure as variáveis de ambiente:
   - Crie um arquivo `.env` na raiz do projeto
   - Adicione as credenciais necessárias para o Bitrix24 (consulte a documentação interna)

4. Execute a aplicação:
```
streamlit run app.py
```

## Configuração

Na primeira execução, o dashboard solicitará a configuração da categoria de dados que deseja monitorar no Bitrix24. É necessário informar o ID da categoria para que a aplicação possa buscar as informações corretas.

## Estrutura do Projeto

```
streamlit_higializacao/
│
├── app.py                     # Arquivo principal da aplicação
│
├── config/                    # Configurações do sistema
│   ├── __init__.py            # Inicializador do pacote
│   └── settings.py            # Configurações e estilos
│
├── data/                      # Processamento de dados
│   ├── __init__.py            # Inicializador do pacote
│   ├── processor.py           # Funções de processamento de dados
│   └── bitrix_service.py      # Serviço de integração com Bitrix24
│
├── ui/                        # Interface de usuário
│   ├── __init__.py            # Inicializador do pacote
│   └── components.py          # Componentes da interface
│
├── visualizations/            # Visualizações e gráficos
│   ├── __init__.py            # Inicializador do pacote
│   └── charts.py              # Funções para geração de gráficos
│
├── utils/                     # Utilitários e funções auxiliares
│   └── __init__.py            # Inicializador do pacote
│
├── logo.svg.svg               # Logo da aplicação
├── intrucoes_connector_bi     # Instruções para conectar ao BI
├── exemplo_requesicao_bitrix24 # Exemplo de requisição para Bitrix24
├── requirements.txt           # Dependências do projeto
└── .gitignore                 # Arquivos ignorados pelo git
```

## Descrição dos Componentes

### Principais Módulos

- **app.py**: Ponto de entrada da aplicação Streamlit, contém a lógica principal do dashboard e gerencia o fluxo de dados
- **config/settings.py**: Configurações globais, constantes, estilos CSS e definições de tema
- **data/processor.py**: Processamento e transformação dos dados para visualização, incluindo criação de tabelas de análise
- **data/bitrix_service.py**: Integração com a API do Bitrix24 para obtenção de dados dos registros
- **ui/components.py**: Componentes reutilizáveis da interface do usuário, como cartões de métricas e formatação de tabelas
- **visualizations/charts.py**: Funções para criação de gráficos e visualizações com Plotly

### Fluxo Principal da Aplicação

1. **Configuração Inicial**: Verificação de configurações e autenticação com o Bitrix24
2. **Obtenção de Dados**: Consulta à API do Bitrix24 para obter registros da categoria configurada
3. **Processamento**: Transformação e agregação dos dados brutos
4. **Exibição do Dashboard**: Apresentação de métricas, gráficos e tabelas de análise
5. **Interatividade**: Filtros e opções de exportação para análise detalhada

## Integração com Bitrix24

Este dashboard integra-se com o Bitrix24 para obter dados em tempo real sobre o processo de higialização. A comunicação é feita através de requisições REST utilizando o módulo `data/bitrix_service.py`.

Para configurar a integração:
1. Obtenha credenciais de acesso à API do Bitrix24
2. Configure o ID da categoria que deseja monitorar na primeira execução do dashboard
3. Os dados serão atualizados automaticamente a cada acesso ou manualmente através do botão de atualização

## Implantação

Este projeto está implantado no Streamlit Cloud e pode ser acessado através do link:
[Dashboard de Higialização](https://streamlit_higializacao.streamlit.app)

## Contato e Suporte

Para dúvidas, sugestões ou problemas, por favor abra uma issue no repositório do GitHub ou entre em contato com a equipe de desenvolvimento. 
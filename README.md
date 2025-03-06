# Dashboard de Higialização

Dashboard desenvolvido em Streamlit para monitoramento e análise do processo de higialização de dados.

## Funcionalidades

- Acompanhamento de status de higialização por responsável
- Contagem de itens pendentes, incompletos e concluídos
- Tabela de pendências detalhada por categoria
- Tabela de produtividade mostrando itens concluídos por categoria
- Visualização de métricas de conversão

## Requisitos

- Python 3.8+
- Streamlit
- Pandas
- Plotly

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

3. Execute a aplicação:
```
streamlit run app.py
```

## Estrutura do Projeto

```
streamlit_higializacao/
│
├── app.py                 # Arquivo principal da aplicação
├── config/                # Configurações do sistema
│   └── settings.py        # Configurações e estilos
│
├── data/                  # Processamento de dados
│   └── processor.py       # Funções de processamento
│
├── ui/                    # Interface de usuário
│   └── components.py      # Componentes da interface
│
└── requirements.txt       # Dependências do projeto
```

## Implantação

Este projeto está implantado no Streamlit Cloud e pode ser acessado através do link:
[Dashboard de Higialização](https://streamlit_higializacao.streamlit.app) 
## Projeto de Controle de Estacionamento

### Descrição

Este projeto é um sistema de controle de estacionamento desenvolvido com Streamlit, banco de dados MongoDB e Poetry como gestor de dependências. 
O sistema permite registrar a entrada e saída de veículos, consultar veículos estacionados, visualizar o histórico de movimentos e gerenciar configurações como os preços de estacionamento. 
Ele inclui um dashboard para visualizar o faturamento e distribuição de veículos por tipo.

### Recursos do Sistema

1. **Registro de Entrada e Saída**: Registra a entrada e saída de veículos, calculando automaticamente o custo com base no tempo de permanência.
2. **Consulta de Veículos Estacionados**: Mostra todos os veículos atualmente estacionados com opções para registrar saída.
3. **Histórico de Movimentos**: Permite visualizar o histórico completo de entradas e saídas de veículos.
4. **Configurações do Sistema**: Administração dos preços por hora para diferentes tipos de veículos e outras configurações do sistema.
5. **Dashboard de Faturamento**: Exibe o faturamento total em um período especificado e a distribuição dos veículos por tipo.

### Pré-requisitos

- Python 3.12.x
- MongoDB
- Poetry para gerenciamento de dependências

### Instalação

#### Clonando o repositório

Para obter o projeto, clone o repositório em sua máquina local usando:

```bash
git clone https://github.com/filipemsilv4/OpenStParkingLot.git
cd OpenStParkingLot
```

#### Configurando o ambiente com Poetry

Instale o Poetry globalmente em seu sistema (se ainda não estiver instalado):

```bash
pip install poetry
```

Dentro do diretório do projeto, configure o ambiente virtual e instale as dependências:

```bash
poetry install
```

Ative o ambiente virtual gerado pelo Poetry:

```bash
poetry shell
```

#### Configurando o MongoDB

1. Crie uma conta e um cluster gratuito no [MongoDB Atlas](https://www.mongodb.com/cloud/atlas) ou configure um servidor MongoDB local.
2. Obtenha a string de conexão para o seu cluster.

#### Configurações do Streamlit

Crie o arquivo `.streamlit/secrets.toml` baseado no template `template_secrets.toml` encontrado na raiz do projeto. Adicione a string de conexão do MongoDB como mostrado abaixo:

```toml
# .streamlit/secrets.toml
[mongo]
uri = "sua_string_de_conexao_aqui"
```

### Executando o Sistema

Com o ambiente configurado e ativo, execute o aplicativo Streamlit usando:

```bash
streamlit run app.py
```

O sistema agora deve estar rodando localmente em `http://localhost:8501`, e você pode visualizar e interagir com a interface do controle de estacionamento.

### Suporte

Para problemas, sugestões ou contribuições, por favor, abra uma issue no repositório do GitHub.

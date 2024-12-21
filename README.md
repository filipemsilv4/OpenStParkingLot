# OpenStParkingLot - Sistema de Controle de Estacionamento

[![Deploy no Streamlit Community Cloud](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://openstparkinglot.streamlit.app/)

## Descrição

Este projeto é um sistema de controle de estacionamento desenvolvido com Streamlit, banco de dados MongoDB e Poetry como gestor de dependências. O sistema permite registrar a entrada e saída de veículos, consultar veículos estacionados, visualizar o histórico de movimentos e gerenciar configurações como os preços de estacionamento. Ele inclui um dashboard para visualizar o faturamento e distribuição de veículos por tipo.

Você pode testar o sistema diretamente na URL: [https://openstparkinglot.streamlit.app/](https://openstparkinglot.streamlit.app/), que está hospedada no Streamlit Community Cloud. Basta seguir o passo a passo mais abaixo para gerar a sua string de conexão. 

## Recursos do Sistema

1. **Registro de Entrada e Saída**: Registra a entrada e saída de veículos, calculando automaticamente o custo com base no tempo de permanência.
2. **Consulta de Veículos Estacionados**: Mostra todos os veículos atualmente estacionados com opções para registrar saída.
3. **Histórico de Movimentos**: Permite visualizar o histórico completo de entradas e saídas de veículos.
4. **Configurações do Sistema**: Administração dos preços por hora para diferentes tipos de veículos e outras configurações do sistema.
5. **Dashboard de Faturamento**: Exibe o faturamento total em um período especificado e a distribuição dos veículos por tipo.

## Configuração do MongoDB Atlas

Antes de executar o projeto, é crucial configurar corretamente o MongoDB Atlas. Siga os passos abaixo cuidadosamente:

### 1. Criando uma Conta e um Cluster no MongoDB Atlas

*   Acesse o [MongoDB Atlas](https://www.mongodb.com/cloud/atlas) e crie uma conta gratuita.
*   Após criar a conta, crie um novo cluster gratuito (shared cluster).

### 2. Configurando o Acesso de Qualquer IP (Whitelist)

*   No painel do MongoDB Atlas, vá para a seção **Network Access** (Acesso de Rede), localizada na aba **Security** (Segurança).
*   Clique em **Add IP Address** (Adicionar Endereço IP).
*   Selecione **Allow Access from Anywhere** (Permitir Acesso de Qualquer Lugar) para adicionar o endereço IP `0.0.0.0/0` à whitelist. Isso permite que qualquer IP se conecte ao seu banco de dados.
*   Clique em **Confirm** (Confirmar).

### 3. Criando um Usuário do Banco de Dados

*   Ainda na aba **Security** (Segurança), vá para a seção **Database Access** (Acesso ao Banco de Dados).
*   Clique em **Add New Database User** (Adicionar Novo Usuário do Banco de Dados).
*   Escolha o método de autenticação **Password** (Senha).
*   Insira um nome de usuário e uma senha forte.
*   Em **Database User Privileges** (Privilégios do Usuário do Banco de Dados), selecione a opção  `Atlas admin`.
*   Clique em **Add User** (Adicionar Usuário).

**Nota:** Anote o nome de usuário e a senha, pois você precisará deles para a string de conexão.

### 4. Obtendo a String de Conexão

*   Na página principal do seu cluster, clique em **Connect** (Conectar).
*   Selecione **Connect your application** (Conectar sua aplicação).
*   Escolha o driver **Python**.
*   Copie a string de conexão fornecida.

A string de conexão começará com:

```
mongodb+srv://<db_username>:<db_password>
```

*   Copie a string de conexão inteira.
*   Substitua `<db_username>` e `<db_password>` pelo nome de usuário e senha que você criou anteriormente.
*   Cole a string de conexão no app e clique em "Conectar"

## Pré-requisitos para rodar localmente

*   Python 3.12.x
*   MongoDB Atlas configurado conforme as instruções acima
*   Poetry para gerenciamento de dependências

## Instalação (para rodar localmente)

### Clonando o Repositório

Clone o repositório para sua máquina local:

```bash
git clone https://github.com/filipemsilv4/OpenStParkingLot.git
cd OpenStParkingLot
```

### Configurando o Ambiente com Poetry

Instale o Poetry (se ainda não estiver instalado):

```bash
pip install poetry
```

Instale as dependências do projeto:

```bash
poetry install
```

Ative o ambiente virtual:

```bash
poetry shell
```

## Executando o Sistema Localmente

Com o ambiente configurado e ativo, execute o aplicativo Streamlit:

```bash
streamlit run app.py
```

O sistema estará disponível no link mostrado no terminal.

## Suporte

Para problemas, sugestões ou contribuições, por favor, abra uma issue no repositório do GitHub.

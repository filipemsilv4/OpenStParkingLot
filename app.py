# app.py
import streamlit as st
from pymongo import MongoClient
from datetime import datetime, timedelta
import pandas as pd
from st_keyup import st_keyup
from controllers.vehicle_controller import (
    registrar_entrada,
    preparar_saida,
    registrar_saida,
    remover_veiculo
)
from controllers.pricing_controller import load_config, save_config
from models.vehicle import normalize_vehicle_data
from utils.helpers import calcular_valor

st.set_page_config(page_title="Controle de Estacionamento", layout="wide")

TIPOS_VEICULOS = {
    "Carro": "🚗",
    "Moto": "🏍️",
    "Caminhão": "🚛",
    "Van": "🚐",
    "Bicicleta": "🚲"
}

def show_connection_form():
    """
    Exibe um formulário para o usuário inserir a string de conexão do MongoDB
    e salva essa string em st.session_state.
    """
    st.error("Não foi possível conectar ao MongoDB. Forneça a URI válida abaixo.")

    with st.form("connection_form"):
        connection_string = st.text_input(
            "String de conexão MongoDB:",
            type="password",
            help="Exemplo: mongodb://usuario:senha@host:27017/banco"
        )
        submitted = st.form_submit_button("Conectar")

        if submitted:
            if connection_string.strip():
                st.session_state.connection_string = connection_string.strip()
                st.success("String de conexão salva. Tentando reconectar...")
                st.rerun()
            else:
                st.error("A string de conexão não pode estar vazia.")

def init_connection():
    """
    Lê a string de conexão do st.session_state e inicializa o MongoClient.
    Retorna o objeto client para ser usado globalmente.
    """
    mongo_uri = st.session_state.get("connection_string")
    if not mongo_uri:
        raise ValueError("String de conexão não configurada em st.session_state.")
    return MongoClient(mongo_uri)

# Inicializa estados necessários
if 'connection_tried' not in st.session_state:
    st.session_state.connection_tried = False

if 'PRECO_POR_HORA' not in st.session_state:
    st.session_state.PRECO_POR_HORA = {
        "Carro": 10.0,
        "Moto": 5.0,
        "Caminhão": 15.0,
        "Van": 12.0,
        "Bicicleta": 2.0
    }

# Tenta conectar ao MongoDB com a URI armazenada
try:
    client = init_connection()
    client.server_info()  # Verifica se a conexão funciona
    db = client.estacionamento
    collection = db.veiculos
    config_collection = db.configuracoes
except Exception as e:
    st.error(f"Erro ao conectar no MongoDB: {e}")
    show_connection_form()
    st.stop()

# Tenta carregar as configurações de preços
try:
    load_config(config_collection)
except Exception as e:
    st.error(f"Não foi possível carregar as configurações de preço: {e}")

if 'last_plate' not in st.session_state:
    st.session_state.last_plate = ""
if 'entrada_datetime' not in st.session_state:
    st.session_state.entrada_datetime = datetime.now()
if 'show_exit_dialog' not in st.session_state:
    st.session_state.show_exit_dialog = False
if 'selected_vehicle' not in st.session_state:
    st.session_state.selected_vehicle = None

def update_datetime():
    """
    Atualiza a data e hora de entrada caso a placa digitada seja diferente
    da última placa registrada.
    """
    if st.session_state.placa_entrada != st.session_state.last_plate:
        st.session_state.entrada_datetime = datetime.now()
        st.session_state.last_plate = st.session_state.placa_entrada

st.title("📋 Controle de Estacionamento")

tab1, tab2, tab3, tab4 = st.tabs(["Movimento", "Dashboard", "Histórico", "Configurações"])

# -----------------------------------------
# TAB 1 - Movimento (Entrada e Lista de Veículos Estacionados)
# -----------------------------------------
with tab1:
    col1, col2 = st.columns(2)

    # Seção de Registrar Entrada
    with col1:
        st.subheader("Registrar Entrada")

        placa_input = st.text_input(
            "Digite a placa do veículo:",
            key="placa_entrada",
            on_change=update_datetime
        )

        tipo_veiculo = st.selectbox(
            "Tipo de veículo:",
            options=list(TIPOS_VEICULOS.keys()),
            key="tipo_veiculo"
        )

        col_data, col_hora = st.columns(2)
        with col_data:
            data_entrada = st.date_input(
                "Data de entrada:",
                value=st.session_state.entrada_datetime.date(),
                key="data_entrada"
            )
        with col_hora:
            hora_entrada = st.time_input(
                "Hora de entrada:",
                value=st.session_state.entrada_datetime.time(),
                key="hora_entrada"
            )

        datetime_entrada = datetime.combine(data_entrada, hora_entrada)

        if st.button("Registrar Entrada", type="primary"):
            if not placa_input.strip():
                st.error("Por favor, informe a placa do veículo.")
            else:
                try:
                    message = registrar_entrada(
                        collection,
                        placa_input.upper().strip(),
                        tipo_veiculo,
                        datetime_entrada
                    )
                    st.success(message)
                    st.rerun()
                except Exception as e:
                    st.error(f"Ocorreu um erro ao registrar a entrada: {e}")

    # Seção de Veículos Estacionados
    with col2:
        st.subheader("Veículos Estacionados")
        busca_placa = st_keyup("🔍 Buscar placa:", key="0").upper()

        query = {"status": "estacionado"}
        if busca_placa:
            query["placa"] = {"$regex": busca_placa, "$options": "i"}

        try:
            veiculos = list(collection.find(query))
        except Exception as e:
            st.error(f"Não foi possível buscar veículos estacionados: {e}")
            veiculos = []

        if not veiculos:
            if busca_placa:
                st.info(f"Nenhum veículo encontrado com a placa contendo '{busca_placa}'.")
            else:
                st.info("Não há veículos estacionados no momento.")
        else:
            for veiculo in veiculos:
                emoji = TIPOS_VEICULOS.get(veiculo.get('tipo_veiculo', 'Carro'), '🚗')
                with st.expander(f"{emoji} {veiculo['placa']}"):
                    st.write(f"Tipo: {veiculo.get('tipo_veiculo', 'Não especificado')}")
                    st.write(f"Entrada: {veiculo['entrada'].strftime('%d/%m/%Y %H:%M:%S')}")

                    try:
                        valor = calcular_valor(
                            veiculo['entrada'],
                            datetime.now(),
                            veiculo['tipo_veiculo'],
                            st.session_state.PRECO_POR_HORA
                        )
                        st.write(f"Valor a pagar (se sair agora): R$ {valor:.2f}")
                    except Exception as e:
                        st.error(f"Erro ao calcular valor estimado: {e}")
                        valor = 0

                    if st.button(f"Registrar Saída {veiculo['placa']}", key=f"saida_{veiculo['placa']}", type="primary"):
                        try:
                            st.session_state.selected_vehicle = preparar_saida(veiculo)
                            st.session_state.show_exit_dialog = True
                            st.rerun()
                        except Exception as e:
                            st.error(f"Não foi possível preparar a saída: {e}")

# -----------------------------------------
# TAB 2 - Dashboard (Faturamento)
# -----------------------------------------
with tab2:
    st.subheader("Dashboard de Faturamento")

    col_data_inicio, col_data_fim = st.columns(2)
    with col_data_inicio:
        data_inicio = st.date_input(
            "Data inicial:",
            value=datetime.now().date() - timedelta(days=30)
        )
    with col_data_fim:
        data_fim = st.date_input(
            "Data final:",
            value=datetime.now().date()
        )

    inicio = datetime.combine(data_inicio, datetime.min.time())
    fim = datetime.combine(data_fim, datetime.max.time())

    try:
        veiculos_finalizados = list(collection.find({
            "status": "finalizado",
            "saida": {"$gte": inicio, "$lte": fim}
        }))
    except Exception as e:
        st.error(f"Erro ao buscar veículos finalizados: {e}")
        veiculos_finalizados = []

    # Normaliza os dados do veículo para evitar inconsistências
    veiculos_finalizados = [normalize_vehicle_data(v) for v in veiculos_finalizados]
    veiculos_finalizados = [v for v in veiculos_finalizados if v is not None]

    if veiculos_finalizados:
        df = pd.DataFrame(veiculos_finalizados)
        total_faturado = df['valor_cobrado'].sum()

        veiculos_por_tipo = df['tipo_veiculo'].value_counts()

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Faturado", f"R$ {total_faturado:.2f}")
        with col2:
            st.metric("Quantidade de Veículos", len(veiculos_finalizados))
        with col3:
            ticket_medio = total_faturado / len(veiculos_finalizados) if veiculos_finalizados else 0
            st.metric("Ticket Médio", f"R$ {ticket_medio:.2f}")

        st.subheader("Distribuição por Tipo de Veículo")
        st.bar_chart(veiculos_por_tipo)
    else:
        st.info("Nenhum veículo finalizado no período selecionado.")

# -----------------------------------------
# TAB 3 - Histórico de Veículos
# -----------------------------------------
with tab3:
    st.subheader("Histórico de Veículos")

    busca_historico = st_keyup("🔍 Buscar placa no histórico:", key="1").upper()

    query_historico = {"status": "finalizado"}
    if busca_historico:
        query_historico["placa"] = {"$regex": busca_historico, "$options": "i"}

    try:
        historico = list(collection.find(query_historico).sort("saida", -1).limit(50))
    except Exception as e:
        st.error(f"Erro ao buscar histórico de veículos: {e}")
        historico = []

    historico = [normalize_vehicle_data(v) for v in historico]
    historico = [v for v in historico if v is not None]

    if historico:
        for veiculo in historico:
            emoji = TIPOS_VEICULOS.get(veiculo.get('tipo_veiculo', 'Carro'), '🚗')
            saida_str = veiculo['saida'].strftime('%d/%m/%Y %H:%M') if veiculo.get('saida') else "Desconhecido"
            with st.expander(f"{emoji} {veiculo['placa']} - {saida_str}"):
                st.write(f"Tipo: {veiculo.get('tipo_veiculo', 'Não especificado')}")
                st.write(f"Entrada: {veiculo['entrada'].strftime('%d/%m/%Y %H:%M:%S')}")
                st.write(f"Saída: {saida_str}")
                valor = veiculo.get('valor_cobrado', 0.0)
                st.write(f"Valor cobrado: R$ {valor:.2f}")

                # Remoção de veículo do histórico
                confirma_remover = st.text_input(
                    "Digite 'CONFIRMAR' para remover este veículo do histórico:",
                    key=f"remover_{veiculo['_id']}"
                )
                if st.button(f"Remover Veículo {veiculo['_id']}", key=f"btn_remover_{veiculo['_id']}", type="primary"):
                    if confirma_remover == "CONFIRMAR":
                        try:
                            message = remover_veiculo(collection, veiculo['_id'])
                            st.success(message)
                            st.rerun()
                        except Exception as e:
                            st.error(f"Não foi possível remover o veículo: {e}")
                    else:
                        st.error("Para remover, digite exatamente 'CONFIRMAR' no campo acima.")
    else:
        st.info("Nenhum registro encontrado no histórico.")

# -----------------------------------------
# SIDEBAR - Registrar Saída (Dialog de edição) 
# -----------------------------------------
if st.session_state.show_exit_dialog:
    veiculo = st.session_state.selected_vehicle

    if veiculo is None:
        st.sidebar.error("Nenhum veículo selecionado para saída.")
    else:
        if 'saida_data_estado' not in st.session_state:
            st.session_state.saida_data_estado = datetime.now().date()
        if 'saida_hora_estado' not in st.session_state:
            st.session_state.saida_hora_estado = datetime.now().time()

        st.sidebar.header("Registrar Saída")
        st.sidebar.write(f"Veículo: {veiculo['placa']}")

        try:
            tipo_veiculo_edit = st.sidebar.selectbox(
                "Tipo de veículo:",
                options=list(TIPOS_VEICULOS.keys()),
                index=list(TIPOS_VEICULOS.keys()).index(veiculo.get('tipo_veiculo', 'Carro')),
                key="tipo_veiculo_edit"
            )
        except ValueError:
            # Caso o tipo_veiculo não esteja na lista por algum erro
            tipo_veiculo_edit = "Carro"

        entrada_data = st.sidebar.date_input(
            "Data de entrada:",
            value=veiculo['entrada'].date(),
            key="entrada_data_edit"
        )
        entrada_hora = st.sidebar.time_input(
            "Hora de entrada:",
            value=veiculo['entrada'].time(),
            key="entrada_hora_edit"
        )
        entrada_edit = datetime.combine(entrada_data, entrada_hora)

        saida_data = st.sidebar.date_input(
            "Data de saída:",
            value=st.session_state.saida_data_estado,
            key="saida_data_edit"
        )
        saida_hora = st.sidebar.time_input(
            "Hora de saída:",
            value=st.session_state.saida_hora_estado,
            key="saida_hora_edit"
        )

        st.session_state.saida_data_estado = saida_data
        st.session_state.saida_hora_estado = saida_hora

        saida_edit = datetime.combine(saida_data, saida_hora)

        try:
            valor_atualizado = calcular_valor(
                entrada_edit,
                saida_edit,
                tipo_veiculo_edit,
                st.session_state.PRECO_POR_HORA
            )
        except Exception as e:
            st.sidebar.error(f"Erro ao calcular o valor de saída: {e}")
            valor_atualizado = 0.0

        st.sidebar.write(f"Valor a cobrar: R$ {valor_atualizado:.2f}")

        col1, col2 = st.sidebar.columns(2)
        with col1:
            if st.button("Confirmar Saída", type="primary"):
                try:
                    valor_cobrado = calcular_valor(
                        entrada_edit,
                        saida_edit,
                        tipo_veiculo_edit,
                        st.session_state.PRECO_POR_HORA
                    )
                    message = registrar_saida(
                        collection,
                        veiculo['_id'],
                        entrada_edit,
                        saida_edit,
                        tipo_veiculo_edit,
                        valor_cobrado
                    )
                    st.sidebar.success(message)
                except Exception as e:
                    st.sidebar.error(f"Não foi possível registrar a saída: {e}")
                finally:
                    # Em qualquer caso, fechamos o diálogo e limpamos o estado
                    st.session_state.show_exit_dialog = False
                    st.session_state.selected_vehicle = None
                    st.rerun()
        with col2:
            if st.button("Cancelar", type="secondary"):
                st.session_state.show_exit_dialog = False
                st.session_state.selected_vehicle = None
                if 'saida_data_estado' in st.session_state:
                    del st.session_state.saida_data_estado
                if 'saida_hora_estado' in st.session_state:
                    del st.session_state.saida_hora_estado
                st.rerun()

# -----------------------------------------
# TAB 4 - Configurações
# -----------------------------------------
with tab4:
    st.subheader("⚙️ Configurações do Sistema")

    st.write("### Preços por Hora")

    # Carrega a configuração atual do banco
    try:
        precos = load_config(config_collection)
    except Exception as e:
        st.error(f"Erro ao carregar configurações de preço: {e}")
        precos = st.session_state.PRECO_POR_HORA

    novos_precos = {}

    for tipo, emoji in TIPOS_VEICULOS.items():
        col1, col2 = st.columns([3, 1])
        with col1:
            valor_atual = float(precos.get(tipo, st.session_state.PRECO_POR_HORA.get(tipo, 0.0)))
            novos_precos[tipo] = st.number_input(
                f"{emoji} Preço por hora para {tipo}:",
                min_value=0.0,
                value=valor_atual,
                step=0.5,
                format="%.2f"
            )

    if st.button("Salvar Preços", type="primary"):
        try:
            save_config(config_collection, novos_precos)
            st.success("Preços atualizados com sucesso!")
            st.rerun()
        except Exception as e:
            st.error(f"Não foi possível salvar as configurações de preço: {e}")

    st.write("### Gerenciamento do Banco de Dados")
    st.warning("⚠️ Atenção: As ações abaixo são irreversíveis!")

    with st.expander("🗑️ Limpar Banco de Dados"):
        st.write("Esta ação irá apagar todos os registros de veículos do banco de dados (histórico e atuais).")
        st.write("Os preços configurados serão mantidos.")

        confirma_texto = st.text_input(
            "Digite 'CONFIRMAR' para limpar o banco de dados:",
            key="confirma_limpar"
        )

        if st.button("Limpar Banco de Dados", type="primary", key="btn_limpar"):
            if confirma_texto == "CONFIRMAR":
                try:
                    collection.delete_many({})
                    st.success("Banco de dados limpo com sucesso!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Não foi possível limpar o banco de dados: {e}")
            else:
                st.error("Por favor, digite 'CONFIRMAR' para prosseguir com a limpeza do banco de dados.")
# app.py
import streamlit as st
from pymongo import MongoClient
from datetime import datetime, timedelta
import pandas as pd
from st_keyup import st_keyup
import os

from config.connection import save_connection_string, init_connection
from controllers.vehicle_controller import registrar_entrada, preparar_saida, registrar_saida, remover_veiculo
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

if 'PRECO_POR_HORA' not in st.session_state:
    st.session_state.PRECO_POR_HORA = {
        "Carro": 10.0,
        "Moto": 5.0,
        "Caminhão": 15.0,
        "Van": 12.0,
        "Bicicleta": 2.0
    }

def show_connection_form():
    st.error("Não foi possível conectar ao MongoDB. Por favor, forneça uma string de conexão válida.")

    with st.form("connection_form"):
        connection_string = st.text_input(
            "String de conexão MongoDB:",
            type="password",
            help="Formato: mongodb://username:password@host:port/database"
        )
        submitted = st.form_submit_button("Conectar")

        if submitted and connection_string:
            if save_connection_string(connection_string):
                st.session_state.connection_tried = True
                st.success("String de conexão salva com sucesso! Por favor, reinicie a aplicação manualmente (Ctrl+C e execute novamente).")
                st.stop()

if 'connection_tried' not in st.session_state:
    st.session_state.connection_tried = False

try:
    if st.session_state.connection_tried:
        st.warning("Por favor, reinicie a aplicação manualmente para aplicar a nova configuração.")
        st.stop()

    client = init_connection()
    client.server_info()
    db = client.estacionamento
    collection = db.veiculos
    config_collection = db.configuracoes
except Exception as e:
    show_connection_form()
    st.stop()

load_config(config_collection)

if 'last_plate' not in st.session_state:
    st.session_state.last_plate = ""
if 'entrada_datetime' not in st.session_state:
    st.session_state.entrada_datetime = datetime.now()
if 'show_exit_dialog' not in st.session_state:
    st.session_state.show_exit_dialog = False
if 'selected_vehicle' not in st.session_state:
    st.session_state.selected_vehicle = None

def update_datetime():
    if st.session_state.placa_entrada != st.session_state.last_plate:
        st.session_state.entrada_datetime = datetime.now()
        st.session_state.last_plate = st.session_state.placa_entrada

st.title("📋 Controle de Estacionamento")

tab1, tab2, tab3, tab4 = st.tabs(["Movimento", "Dashboard", "Histórico", "Configurações"])

with tab1:
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Registrar Entrada")

        placa_input = st.text_input("Digite a placa do veículo:", key="placa_entrada", on_change=update_datetime)

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
            message = registrar_entrada(collection, placa_input.upper(), tipo_veiculo, datetime_entrada)
            st.info(message)
            st.rerun()

    with col2:
        st.subheader("Veículos Estacionados")
        busca_placa = st_keyup("🔍 Buscar placa:", key="0").upper()

        query = {"status": "estacionado"}
        if busca_placa:
            query["placa"] = {"$regex": busca_placa, "$options": "i"}

        veiculos = list(collection.find(query))

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

                    valor = calcular_valor(veiculo['entrada'], datetime.now(), veiculo['tipo_veiculo'], st.session_state.PRECO_POR_HORA)
                    st.write(f"Valor a pagar (se sair agora): R$ {valor:.2f}")

                    if st.button("Registrar Saída", key=veiculo['placa'], type="primary"):
                        st.session_state.selected_vehicle = preparar_saida(veiculo)
                        st.session_state.show_exit_dialog = True
                        st.rerun()

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

    veiculos_finalizados = list(collection.find({
        "status": "finalizado",
        "saida": {"$gte": inicio, "$lte": fim}
    }))

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

with tab3:
    st.subheader("Histórico de Veículos")

    busca_historico = st_keyup("🔍 Buscar placa no histórico:", key="1").upper()

    query_historico = {"status": "finalizado"}
    if busca_historico:
        query_historico["placa"] = {"$regex": busca_historico, "$options": "i"}

    historico = list(collection.find(query_historico).sort("saida", -1).limit(50))
    historico = [normalize_vehicle_data(v) for v in historico]
    historico = [v for v in historico if v is not None]

    if historico:
        for veiculo in historico:
            emoji = TIPOS_VEICULOS.get(veiculo.get('tipo_veiculo', 'Carro'), '🚗')
            with st.expander(f"{emoji} {veiculo['placa']} - {veiculo['saida'].strftime('%d/%m/%Y %H:%M')}"):
                st.write(f"Tipo: {veiculo.get('tipo_veiculo', 'Não especificado')}")
                st.write(f"Entrada: {veiculo['entrada'].strftime('%d/%m/%Y %H:%M:%S')}")
                st.write(f"Saída: {veiculo['saida'].strftime('%d/%m/%Y %H:%M:%S')}")
                valor = veiculo.get('valor_cobrado', 0.0)
                st.write(f"Valor cobrado: R$ {valor:.2f}")

                # Remoção de veículo
                confirma_remover = st.text_input(
                    "Digite 'CONFIRMAR' para remover este veículo do histórico:",
                    key=f"remover_{veiculo['_id']}"
                )
                if st.button("Remover Veículo", key=f"btn_remover_{veiculo['_id']}", type="primary"):
                    if confirma_remover == "CONFIRMAR":
                        message = remover_veiculo(collection, veiculo['_id'])
                        st.success(message)
                        st.rerun()
                    else:
                        st.error("Por favor, digite 'CONFIRMAR' para remover o veículo.")
    else:
        st.info("Nenhum registro encontrado no histórico.")

if st.session_state.show_exit_dialog:
    veiculo = st.session_state.selected_vehicle

    if 'saida_data_estado' not in st.session_state:
        st.session_state.saida_data_estado= datetime.now().date()
    if 'saida_hora_estado' not in st.session_state:
        st.session_state.saida_hora_estado = datetime.now().time()

    st.sidebar.header("Registrar Saída")
    st.sidebar.write(f"Veículo: {veiculo['placa']}")

    tipo_veiculo_edit = st.sidebar.selectbox(
        "Tipo de veículo:",
        options=list(TIPOS_VEICULOS.keys()),
        index=list(TIPOS_VEICULOS.keys()).index(veiculo.get('tipo_veiculo', 'Carro')),
        key="tipo_veiculo_edit"
    )

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

    valor_atualizado = calcular_valor(entrada_edit, saida_edit, tipo_veiculo_edit, st.session_state.PRECO_POR_HORA)
    st.sidebar.write(f"Valor a cobrar: R$ {valor_atualizado:.2f}")

    col1, col2 = st.sidebar.columns(2)
    with col1:
        if st.button("Confirmar Saída", type="primary"):
            valor_cobrado = calcular_valor(entrada_edit, saida_edit, tipo_veiculo_edit, st.session_state.PRECO_POR_HORA)
            message = registrar_saida(collection, veiculo['_id'], entrada_edit, saida_edit, tipo_veiculo_edit, valor_cobrado)
            st.sidebar.success(message)
            st.session_state.show_exit_dialog = False
            st.session_state.selected_vehicle = None
            st.rerun()
    with col2:
        if st.button("Cancelar", type="secondary"):
            if 'saida_data_estado' in st.session_state:
                del st.session_state.saida_data_estado
            if 'saida_hora_estado' in st.session_state:
                del st.session_state.saida_hora_estado
            st.session_state.show_exit_dialog = False
            st.session_state.selected_vehicle = None
            st.rerun()

with tab4:
    st.subheader("⚙️ Configurações do Sistema")

    st.write("### Preços por Hora")

    precos = load_config(config_collection)
    novos_precos = {}

    for tipo, emoji in TIPOS_VEICULOS.items():
        col1, col2 = st.columns([3, 1])
        with col1:
            novos_precos[tipo] = st.number_input(
                f"{emoji} Preço por hora para {tipo}:",
                min_value=0.0,
                value=float(precos.get(tipo, 0.0)),
                step=0.5,
                format="%.2f"
            )

    if st.button("Salvar Preços", type="primary"):
        save_config(config_collection, novos_precos)
        st.success("Preços atualizados com sucesso!")
        st.rerun()

    st.write("### Gerenciamento do Banco de Dados")
    st.warning("⚠️ Atenção: As ações abaixo são irreversíveis!")

    with st.expander("🗑️ Limpar Banco de Dados"):
        st.write("Esta ação irá apagar todos os registros de veículos do banco de dados.")
        st.write("Os preços configurados serão mantidos.")

        confirma_texto = st.text_input(
            "Digite 'CONFIRMAR' para limpar o banco de dados:",
            key="confirma_limpar"
        )

        if st.button("Limpar Banco de Dados", type="primary", key="btn_limpar"):
            if confirma_texto == "CONFIRMAR":
                collection.delete_many({})
                st.success("Banco de dados limpo com sucesso!")
                st.rerun()
            else:
                st.error("Por favor, digite 'CONFIRMAR' para prosseguir com a limpeza do banco de dados.")
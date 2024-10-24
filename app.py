import streamlit as st
from pymongo import MongoClient
from datetime import datetime, timedelta
import pandas as pd
from st_keyup import st_keyup

# Configuração da página
st.set_page_config(page_title="Controle de Estacionamento", layout="wide")

# Dicionário de tipos de veículos e seus emojis
TIPOS_VEICULOS = {
    "Carro": "🚗",
    "Moto": "🏍️",
    "Caminhão": "🚛",
    "Van": "🚐",
    "Bicicleta": "🚲"
}

# Inicializar preços no session_state se não existirem
if 'PRECO_POR_HORA' not in st.session_state:
    st.session_state.PRECO_POR_HORA = {
        "Carro": 10.0,
        "Moto": 5.0,
        "Caminhão": 15.0,
        "Van": 12.0,
        "Bicicleta": 2.0
    }

# Conectar ao MongoDB
@st.cache_resource
def init_connection():
    return MongoClient(st.secrets["mongo"]["uri"])

try:
    client = init_connection()
    db = client.estacionamento
    collection = db.veiculos
    config_collection = db.configuracoes
except Exception as e:
    st.error(f"Erro ao conectar ao MongoDB: {e}")
    st.stop()

# Carregar configurações do banco de dados
def load_config():
    config = config_collection.find_one({"type": "price_config"})
    if config and "prices" in config:
        st.session_state.PRECO_POR_HORA = config["prices"]
    return st.session_state.PRECO_POR_HORA

# Salvar configurações no banco de dados
def save_config(prices):
    config_collection.update_one(
        {"type": "price_config"},
        {"$set": {"prices": prices}},
        upsert=True
    )
    st.session_state.PRECO_POR_HORA = prices

# Função para calcular o valor a ser pago
def calcular_valor(entrada, saida, tipo_veiculo):
    preco_hora = st.session_state.PRECO_POR_HORA.get(tipo_veiculo, 10.0)
    
    if isinstance(entrada, str):
        entrada = datetime.fromisoformat(entrada)
    if isinstance(saida, str):
        saida = datetime.fromisoformat(saida)
        
    tempo_permanencia = saida - entrada
    tempo_total_minutos = tempo_permanencia.total_seconds() / 60
    unidades_de_15_minutos = (tempo_total_minutos + 14) // 15
    
    valor_a_pagar = (unidades_de_15_minutos / 4) * preco_hora
    return max(valor_a_pagar, preco_hora/4)

# Função para garantir que todos os campos necessários existam
def normalize_vehicle_data(veiculo):
    if not isinstance(veiculo, dict):
        return None
    
    defaults = {
        'tipo_veiculo': 'Carro',  # Tipo padrão
        'placa': 'DESCONHECIDO',
        'entrada': datetime.now(),
        'status': 'finalizado',
        'saida': datetime.now(),
    }
    
    # Garantir que todos os campos existam
    for key, default_value in defaults.items():
        if key not in veiculo or veiculo[key] is None:
            veiculo[key] = default_value
    
    return veiculo

# Inicializar estado da sessão
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

# Função de callback para atualização da busca
def on_search_change():
    # Não precisamos fazer nada aqui pois o Streamlit já vai reexecutar o app
    pass

# Função para registrar entrada
def registrar_entrada(placa, tipo_veiculo, hora_entrada):
    if not placa:
        st.warning("Por favor, digite uma placa válida!")
        return
    
    veiculo = collection.find_one({"placa": placa, "status": "estacionado"})
    if veiculo:
        st.warning(f"Veículo com placa {placa} já está estacionado!")
        return
    
    entrada = {
        "placa": placa,
        "tipo_veiculo": tipo_veiculo,
        "entrada": hora_entrada,
        "status": "estacionado"
    }
    collection.insert_one(entrada)
    st.success(f"Entrada registrada para o veículo {placa}")

# Função para preparar registro de saída
def preparar_saida(veiculo):
    st.session_state.show_exit_dialog = True
    st.session_state.selected_vehicle = veiculo
    st.rerun()

# Função para registrar saída com dados editados
def registrar_saida(veiculo_id, entrada, saida, tipo_veiculo):
    valor_final = calcular_valor(entrada, saida, tipo_veiculo)
    
    collection.update_one(
        {"_id": veiculo_id},
        {
            "$set": {
                "saida": saida,
                "status": "finalizado",
                "tipo_veiculo": tipo_veiculo,
                "entrada": entrada,
                "valor_cobrado": valor_final
            }
        }
    )
    st.session_state.show_exit_dialog = False
    st.session_state.selected_vehicle = None
    st.success(f"Saída registrada. Valor cobrado: R$ {valor_final:.2f}")
    st.rerun()

# Título do app
st.title("📋 Controle de Estacionamento")

# Tabs para diferentes seções
tab1, tab2, tab3, tab4 = st.tabs(["Movimento", "Dashboard", "Histórico", "Configurações"])

# Tab de Movimento (entrada/saída)
with tab1:
    col1, col2 = st.columns(2)
    
    # Coluna de entrada
    with col1:
        st.subheader("Registrar Entrada")
        
        placa_input = st.text_input("Digite a placa do veículo:", 
                                   key="placa_entrada", 
                                   on_change=update_datetime)
        
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
            registrar_entrada(placa_input.upper(), tipo_veiculo, datetime_entrada)
            st.rerun()


    # Coluna de veículos estacionados
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
                    
                    valor = calcular_valor(veiculo['entrada'], datetime.now(), veiculo['tipo_veiculo'])
                    st.write(f"Valor a pagar (se sair agora): R$ {valor:.2f}")
                    
                    if st.button("Registrar Saída", key=veiculo['placa'], type="primary"):
                        preparar_saida(veiculo)

# Tab de Dashboard
with tab2:
    st.subheader("Dashboard de Faturamento")
    
    # Filtros de data
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
    
    # Converter datas para datetime
    inicio = datetime.combine(data_inicio, datetime.min.time())
    fim = datetime.combine(data_fim, datetime.max.time())
    
    # Buscar dados do período
    veiculos_finalizados = list(collection.find({
        "status": "finalizado",
        "saida": {"$gte": inicio, "$lte": fim}
    }))
    
    # Normalizar dados
    veiculos_finalizados = [normalize_vehicle_data(v) for v in veiculos_finalizados]
    veiculos_finalizados = [v for v in veiculos_finalizados if v is not None]
    
    if veiculos_finalizados:
        # Calcular métricas
        df = pd.DataFrame(veiculos_finalizados)
        
        total_faturado = sum(calcular_valor(v['entrada'], v['saida'], v['tipo_veiculo']) 
                            for v in veiculos_finalizados)
        
        veiculos_por_tipo = df['tipo_veiculo'].value_counts()
        
        # Exibir métricas
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Faturado", f"R$ {total_faturado:.2f}")
        with col2:
            st.metric("Quantidade de Veículos", len(veiculos_finalizados))
        with col3:
            ticket_medio = total_faturado / len(veiculos_finalizados) if veiculos_finalizados else 0
            st.metric("Ticket Médio", f"R$ {ticket_medio:.2f}")
        
        # Gráfico de veículos por tipo
        st.subheader("Distribuição por Tipo de Veículo")
        st.bar_chart(veiculos_por_tipo)
    else:
        st.info("Nenhum veículo finalizado no período selecionado.")

# Tab de Histórico
with tab3:
    st.subheader("Histórico de Veículos")
    
    # Filtro de placa para histórico
    busca_historico = st_keyup("🔍 Buscar placa no histórico:", key="1").upper()
    
    # Query para histórico
    query_historico = {"status": "finalizado"}
    if busca_historico:
        query_historico["placa"] = {"$regex": busca_historico, "$options": "i"}
    
    # Buscar histórico e normalizar dados
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
                valor = calcular_valor(veiculo['entrada'], veiculo['saida'], veiculo['tipo_veiculo'])
                st.write(f"Valor cobrado: R$ {valor:.2f}")
    else:
        st.info("Nenhum registro encontrado no histórico.")

# Dialog de confirmação de saída
if st.session_state.show_exit_dialog:
    veiculo = st.session_state.selected_vehicle
    
    # Inicializar estados para data e hora de saída se não existirem
    if 'saida_data_estado' not in st.session_state:
        st.session_state.saida_data_estado = datetime.now().date()
    if 'saida_hora_estado' not in st.session_state:
        st.session_state.saida_hora_estado = datetime.now().time()
    
    st.sidebar.header("Registrar Saída")
    st.sidebar.write(f"Veículo: {veiculo['placa']}")
    
    # Campos editáveis
    tipo_veiculo_edit = st.sidebar.selectbox(
        "Tipo de veículo:",
        options=list(TIPOS_VEICULOS.keys()),
        index=list(TIPOS_VEICULOS.keys()).index(veiculo['tipo_veiculo']),
        key="tipo_veiculo_edit"
    )
    
    # Data e hora de entrada
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
    
    # Data e hora de saída usando os estados
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
    
    # Atualizar os estados com os novos valores
    st.session_state.saida_data_estado = saida_data
    st.session_state.saida_hora_estado = saida_hora
    
    saida_edit = datetime.combine(saida_data, saida_hora)
    
    # Calcular e mostrar valor atualizado
    valor_atualizado = calcular_valor(entrada_edit, saida_edit, tipo_veiculo_edit)
    st.sidebar.write(f"Valor a cobrar: R$ {valor_atualizado:.2f}")
    
    # Botões de confirmação
    col1, col2 = st.sidebar.columns(2)
    with col1:
        if st.button("Confirmar Saída", type="primary"):
            registrar_saida(veiculo['_id'], entrada_edit, saida_edit, tipo_veiculo_edit)
    with col2:
        if st.button("Cancelar", type="secondary"):
            # Limpar os estados ao cancelar
            if 'saida_data_estado' in st.session_state:
                del st.session_state.saida_data_estado
            if 'saida_hora_estado' in st.session_state:
                del st.session_state.saida_hora_estado
            st.session_state.show_exit_dialog = False
            st.session_state.selected_vehicle = None
            st.rerun()
            
# Tab de Configurações
with tab4:
    st.subheader("⚙️ Configurações do Sistema")
    
    # Seção de Preços
    st.write("### Preços por Hora")
    
    precos = load_config()
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
        save_config(novos_precos)
        st.success("Preços atualizados com sucesso!")
    
    # Seção de Gerenciamento do Banco de Dados
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

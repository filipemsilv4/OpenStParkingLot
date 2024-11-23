# controllers/pricing_controller.py
import streamlit as st

def load_config(config_collection):
    config = config_collection.find_one({"type": "price_config"})
    if config and "prices" in config:
        st.session_state.PRECO_POR_HORA = config["prices"]
    else:
        st.session_state.PRECO_POR_HORA = {
            "Carro": 10.0,
            "Moto": 5.0,
            "Caminhão": 15.0,
            "Van": 12.0,
            "Bicicleta": 2.0
        }
    return st.session_state.PRECO_POR_HORA

def save_config(config_collection, prices):
    config_collection.update_one(
        {"type": "price_config"},
        {"$set": {"prices": prices}},
        upsert=True
    )
    st.session_state.PRECO_POR_HORA = prices
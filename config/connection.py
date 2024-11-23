# config/connection.py
import os
import toml
import streamlit as st
from pymongo import MongoClient

def save_connection_string(connection_string):
    try:
        project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        streamlit_dir = os.path.join(project_dir, ".streamlit")
        secrets_path = os.path.join(streamlit_dir, "secrets.toml")
        os.makedirs(streamlit_dir, exist_ok=True)

        secrets = toml.load(secrets_path) if os.path.exists(secrets_path) else {}
        secrets.setdefault('mongo', {})['uri'] = connection_string

        with open(secrets_path, "w") as f:
            toml.dump(secrets, f)

        st.success(f"Arquivo secrets.toml criado/atualizado em: {secrets_path}")
        return True
    except Exception as e:
        st.error(f"Erro ao salvar string de conexão: {e}")
        return False

def init_connection():
    if "mongo" not in st.secrets:
        raise Exception("Configuração do MongoDB não encontrada")
    return MongoClient(st.secrets["mongo"]["uri"])
# models/vehicle.py
from datetime import datetime

def normalize_vehicle_data(veiculo):
    if not isinstance(veiculo, dict):
        return None

    defaults = {
        'tipo_veiculo': 'Carro',
        'placa': 'DESCONHECIDO',
        'entrada': datetime.now(),
        'status': 'finalizado',
        'saida': datetime.now(),
    }

    for key, default_value in defaults.items():
        if key not in veiculo or veiculo[key] is None:
            veiculo[key] = default_value

    return veiculo
# controllers/vehicle_controller.py
from datetime import datetime
from utils.helpers import calcular_valor

def registrar_entrada(collection, placa, tipo_veiculo, hora_entrada):
    if not placa:
        return "Por favor, digite uma placa válida!"

    veiculo = collection.find_one({"placa": placa, "status": "estacionado"})
    if veiculo:
        return f"Veículo com placa {placa} já está estacionado!"

    entrada = {
        "placa": placa,
        "tipo_veiculo": tipo_veiculo,
        "entrada": hora_entrada,
        "status": "estacionado"
    }
    collection.insert_one(entrada)
    return f"Entrada registrada para o veículo {placa}"

def preparar_saida(veiculo):
    return veiculo

def registrar_saida(collection, veiculo_id, entrada, saida, tipo_veiculo, valor_cobrado):
    collection.update_one(
        {"_id": veiculo_id},
        {
            "$set": {
                "saida": saida,
                "status": "finalizado",
                "tipo_veiculo": tipo_veiculo,
                "entrada": entrada,
                "valor_cobrado": valor_cobrado
            }
        }
    )
    return f"Saída registrada. Valor cobrado: R$ {valor_cobrado:.2f}"

def remover_veiculo(collection, veiculo_id):
    try:
        result = collection.delete_one({"_id": veiculo_id})
        if result.deleted_count == 1:
            return "Veículo removido com sucesso!"
        else:
            return "Veículo não encontrado ou não pôde ser removido."
    except Exception as e:
        return f"Ocorreu um erro ao remover o veículo: {e}"
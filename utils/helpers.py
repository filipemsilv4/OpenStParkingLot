# utils/helpers.py
from datetime import datetime

def calcular_valor(entrada, saida, tipo_veiculo, precos_por_hora):
    preco_hora = precos_por_hora.get(tipo_veiculo, 10.0)

    if isinstance(entrada, str):
        entrada = datetime.fromisoformat(entrada)
    if isinstance(saida, str):
        saida = datetime.fromisoformat(saida)

    tempo_permanencia = saida - entrada
    tempo_total_minutos = tempo_permanencia.total_seconds() / 60
    unidades_de_15_minutos = (tempo_total_minutos + 14) // 15

    valor_a_pagar = (unidades_de_15_minutos / 4) * preco_hora
    return max(valor_a_pagar, preco_hora/4)
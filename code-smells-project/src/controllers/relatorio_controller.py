"""Casos de uso de relatórios."""
from src.database import get_db
from src.models import relatorio_model

# (faturamento mínimo exclusivo, percentual de desconto), da maior faixa para a menor.
FAIXAS_DESCONTO = ((10000, 0.10), (5000, 0.05), (1000, 0.02))
CASAS_DECIMAIS = 2


def calcular_desconto(faturamento):
    for minimo, percentual in FAIXAS_DESCONTO:
        if faturamento > minimo:
            return faturamento * percentual
    return 0


def vendas():
    resumo = relatorio_model.resumo_vendas(get_db())
    total_pedidos = resumo["total_pedidos"]
    faturamento = resumo["faturamento"]
    desconto = calcular_desconto(faturamento)
    ticket_medio = round(faturamento / total_pedidos, CASAS_DECIMAIS) if total_pedidos > 0 else 0
    return {
        "total_pedidos": total_pedidos,
        "faturamento_bruto": round(faturamento, CASAS_DECIMAIS),
        "desconto_aplicavel": round(desconto, CASAS_DECIMAIS),
        "faturamento_liquido": round(faturamento - desconto, CASAS_DECIMAIS),
        "pedidos_pendentes": resumo["pendentes"],
        "pedidos_aprovados": resumo["aprovados"],
        "pedidos_cancelados": resumo["cancelados"],
        "ticket_medio": ticket_medio,
    }

"""Funções utilitárias genéricas, sem regra de domínio."""
from datetime import datetime, timezone


def utcnow():
    """Data/hora atual em UTC sem tzinfo, no mesmo formato dos valores já gravados no banco."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def calculate_percentage(part, total):
    if total == 0:
        return 0
    return round((part / total) * 100, 2)

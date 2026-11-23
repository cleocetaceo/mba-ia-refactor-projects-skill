"""Operações administrativas sobre o banco."""

# Ordem respeita as dependências (filhos antes dos pais).
_TABELAS_RESET = ("itens_pedido", "pedidos", "produtos", "usuarios")


def limpar_tabelas(db):
    for tabela in _TABELAS_RESET:
        # Nome de tabela vem da constante acima, nunca do cliente.
        db.execute(f"DELETE FROM {tabela}")


def consultar_somente_leitura(db, sql):
    """Executa uma consulta com a conexão em modo somente leitura (defesa em profundidade)."""
    db.execute("PRAGMA query_only = ON")
    try:
        return [dict(row) for row in db.execute(sql).fetchall()]
    finally:
        db.execute("PRAGMA query_only = OFF")

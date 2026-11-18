"""Operações administrativas de banco (acessadas apenas por rotas protegidas)."""

# Ordem respeita dependências: filhos antes dos pais.
TABELAS_RESET = ("itens_pedido", "pedidos", "produtos", "usuarios")


def limpar_tabelas(db):
    for tabela in TABELAS_RESET:
        db.execute(f"DELETE FROM {tabela}")  # nomes fixos, nunca vindos do request


def consultar(db, sql):
    return [dict(row) for row in db.execute(sql).fetchall()]


def executar(db, sql):
    db.execute(sql)

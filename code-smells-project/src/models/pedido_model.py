"""Acesso a dados de pedidos e itens de pedido."""

STATUS_PENDENTE = "pendente"
STATUS_APROVADO = "aprovado"
STATUS_ENVIADO = "enviado"
STATUS_ENTREGUE = "entregue"
STATUS_CANCELADO = "cancelado"
STATUS_VALIDOS = (STATUS_PENDENTE, STATUS_APROVADO, STATUS_ENVIADO, STATUS_ENTREGUE, STATUS_CANCELADO)

PRODUTO_DESCONHECIDO = "Desconhecido"

_SELECT_PEDIDOS_COM_ITENS = """
    SELECT p.id, p.usuario_id, p.status, p.total, p.criado_em,
           i.produto_id, i.quantidade, i.preco_unitario, pr.nome AS produto_nome
    FROM pedidos p
    LEFT JOIN itens_pedido i ON i.pedido_id = p.id
    LEFT JOIN produtos pr ON pr.id = i.produto_id
"""


def _agrupar_itens(rows):
    """Agrupa as linhas do JOIN em pedidos com a lista de itens (sem N+1)."""
    pedidos = {}
    for row in rows:
        pedido = pedidos.setdefault(row["id"], {
            "id": row["id"],
            "usuario_id": row["usuario_id"],
            "status": row["status"],
            "total": row["total"],
            "criado_em": row["criado_em"],
            "itens": [],
        })
        if row["produto_id"] is not None:
            pedido["itens"].append({
                "produto_id": row["produto_id"],
                "produto_nome": row["produto_nome"] or PRODUTO_DESCONHECIDO,
                "quantidade": row["quantidade"],
                "preco_unitario": row["preco_unitario"],
            })
    return list(pedidos.values())


def listar(db, usuario_id=None):
    if usuario_id is None:
        rows = db.execute(_SELECT_PEDIDOS_COM_ITENS + " ORDER BY p.id, i.id").fetchall()
    else:
        rows = db.execute(
            _SELECT_PEDIDOS_COM_ITENS + " WHERE p.usuario_id = ? ORDER BY p.id, i.id", (usuario_id,)
        ).fetchall()
    return _agrupar_itens(rows)


def existe(db, pedido_id):
    return db.execute("SELECT 1 FROM pedidos WHERE id = ?", (pedido_id,)).fetchone() is not None


def inserir(db, usuario_id, total, status=STATUS_PENDENTE):
    cursor = db.execute(
        "INSERT INTO pedidos (usuario_id, status, total) VALUES (?, ?, ?)", (usuario_id, status, total)
    )
    return cursor.lastrowid


def inserir_item(db, pedido_id, produto_id, quantidade, preco_unitario):
    db.execute(
        "INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario) VALUES (?, ?, ?, ?)",
        (pedido_id, produto_id, quantidade, preco_unitario),
    )


def atualizar_status(db, pedido_id, status):
    db.execute("UPDATE pedidos SET status = ? WHERE id = ?", (status, pedido_id))


def contar(db):
    return db.execute("SELECT COUNT(*) FROM pedidos").fetchone()[0]


def resumo_vendas(db):
    """Totais de vendas numa única query agregada."""
    row = db.execute(
        """
        SELECT COUNT(*) AS total_pedidos,
               COALESCE(SUM(total), 0) AS faturamento,
               COALESCE(SUM(CASE WHEN status = ? THEN 1 ELSE 0 END), 0) AS pendentes,
               COALESCE(SUM(CASE WHEN status = ? THEN 1 ELSE 0 END), 0) AS aprovados,
               COALESCE(SUM(CASE WHEN status = ? THEN 1 ELSE 0 END), 0) AS cancelados
        FROM pedidos
        """,
        (STATUS_PENDENTE, STATUS_APROVADO, STATUS_CANCELADO),
    ).fetchone()
    return dict(row)

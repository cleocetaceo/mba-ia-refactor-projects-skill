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
           i.produto_id, i.quantidade, i.preco_unitario,
           pr.id AS produto_encontrado, pr.nome AS produto_nome
    FROM pedidos p
    LEFT JOIN itens_pedido i ON i.pedido_id = p.id
    LEFT JOIN produtos pr ON pr.id = i.produto_id
"""


def _agrupar(rows):
    pedidos = {}
    for row in rows:
        pedido = pedidos.get(row["id"])
        if pedido is None:
            pedido = {
                "id": row["id"],
                "usuario_id": row["usuario_id"],
                "status": row["status"],
                "total": row["total"],
                "criado_em": row["criado_em"],
                "itens": [],
            }
            pedidos[row["id"]] = pedido
        if row["produto_id"] is not None:
            pedido["itens"].append({
                "produto_id": row["produto_id"],
                "produto_nome": row["produto_nome"] if row["produto_encontrado"] is not None else PRODUTO_DESCONHECIDO,
                "quantidade": row["quantidade"],
                "preco_unitario": row["preco_unitario"],
            })
    return list(pedidos.values())


def listar(db, usuario_id=None):
    """Pedidos com itens numa única query (JOIN), opcionalmente filtrados por usuário."""
    if usuario_id is None:
        rows = db.execute(_SELECT_PEDIDOS_COM_ITENS + " ORDER BY p.id, i.id").fetchall()
    else:
        rows = db.execute(
            _SELECT_PEDIDOS_COM_ITENS + " WHERE p.usuario_id = ? ORDER BY p.id, i.id", (usuario_id,)
        ).fetchall()
    return _agrupar(rows)


def inserir(db, usuario_id, total, status=STATUS_PENDENTE):
    cursor = db.execute(
        "INSERT INTO pedidos (usuario_id, status, total) VALUES (?, ?, ?)",
        (usuario_id, status, total),
    )
    return cursor.lastrowid


def inserir_item(db, pedido_id, produto_id, quantidade, preco_unitario):
    db.execute(
        "INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario) VALUES (?, ?, ?, ?)",
        (pedido_id, produto_id, quantidade, preco_unitario),
    )


def atualizar_status(db, pedido_id, status):
    """Retorna False se o pedido não existe."""
    cursor = db.execute("UPDATE pedidos SET status = ? WHERE id = ?", (status, pedido_id))
    return cursor.rowcount > 0

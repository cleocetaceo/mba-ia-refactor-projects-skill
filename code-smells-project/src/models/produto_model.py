"""Acesso a dados de produtos."""

CATEGORIAS_VALIDAS = ("informatica", "moveis", "vestuario", "geral", "eletronicos", "livros")
CATEGORIA_PADRAO = "geral"
NOME_MIN_LEN = 2
NOME_MAX_LEN = 200

PRODUTO_ATIVO = 1
PRODUTO_INATIVO = 0

_CAMPOS = ("id", "nome", "descricao", "preco", "estoque", "categoria", "ativo", "criado_em")


def _to_dict(row):
    return {campo: row[campo] for campo in _CAMPOS}


def listar(db):
    rows = db.execute("SELECT * FROM produtos WHERE ativo = ? ORDER BY id", (PRODUTO_ATIVO,)).fetchall()
    return [_to_dict(row) for row in rows]


def buscar_por_id(db, produto_id):
    row = db.execute(
        "SELECT * FROM produtos WHERE id = ? AND ativo = ?", (produto_id, PRODUTO_ATIVO)
    ).fetchone()
    return _to_dict(row) if row else None


def buscar_por_ids(db, produto_ids):
    """Retorna {id: produto} para os produtos ativos informados (uma única query)."""
    ids = sorted(set(produto_ids))
    if not ids:
        return {}
    placeholders = ", ".join("?" for _ in ids)
    rows = db.execute(
        f"SELECT * FROM produtos WHERE ativo = ? AND id IN ({placeholders})", (PRODUTO_ATIVO, *ids)
    ).fetchall()
    return {row["id"]: _to_dict(row) for row in rows}


def pesquisar(db, termo=None, categoria=None, preco_min=None, preco_max=None):
    clausulas, params = ["ativo = ?"], [PRODUTO_ATIVO]
    if termo:
        clausulas.append("(nome LIKE ? OR descricao LIKE ?)")
        params += [f"%{termo}%", f"%{termo}%"]
    if categoria:
        clausulas.append("categoria = ?")
        params.append(categoria)
    if preco_min:
        clausulas.append("preco >= ?")
        params.append(preco_min)
    if preco_max:
        clausulas.append("preco <= ?")
        params.append(preco_max)
    rows = db.execute(
        f"SELECT * FROM produtos WHERE {' AND '.join(clausulas)} ORDER BY id", params
    ).fetchall()
    return [_to_dict(row) for row in rows]


def criar(db, nome, descricao, preco, estoque, categoria):
    cursor = db.execute(
        "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) VALUES (?, ?, ?, ?, ?)",
        (nome, descricao, preco, estoque, categoria),
    )
    return cursor.lastrowid


def atualizar(db, produto_id, nome, descricao, preco, estoque, categoria):
    db.execute(
        "UPDATE produtos SET nome = ?, descricao = ?, preco = ?, estoque = ?, categoria = ? WHERE id = ?",
        (nome, descricao, preco, estoque, categoria, produto_id),
    )


def desativar(db, produto_id):
    """Exclusão lógica: o produto some do catálogo, mas os itens de pedido continuam íntegros."""
    db.execute("UPDATE produtos SET ativo = ? WHERE id = ?", (PRODUTO_INATIVO, produto_id))


def baixar_estoque(db, produto_id, quantidade):
    """Baixa atômica: só altera se houver estoque suficiente. Retorna False caso contrário."""
    cursor = db.execute(
        "UPDATE produtos SET estoque = estoque - ? WHERE id = ? AND ativo = ? AND estoque >= ?",
        (quantidade, produto_id, PRODUTO_ATIVO, quantidade),
    )
    return cursor.rowcount == 1


def contar(db):
    return db.execute("SELECT COUNT(*) FROM produtos WHERE ativo = ?", (PRODUTO_ATIVO,)).fetchone()[0]

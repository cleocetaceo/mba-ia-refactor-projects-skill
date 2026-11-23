"""Acesso a dados de produtos. Todas as funções recebem a conexão (injeção de dependência)."""

CATEGORIAS_VALIDAS = ("informatica", "moveis", "vestuario", "geral", "eletronicos", "livros")
CATEGORIA_PADRAO = "geral"
NOME_MIN = 2
NOME_MAX = 200

_CAMPOS = ("id", "nome", "descricao", "preco", "estoque", "categoria", "ativo", "criado_em")


def _para_dict(row):
    return {campo: row[campo] for campo in _CAMPOS}


def listar(db):
    return [_para_dict(row) for row in db.execute("SELECT * FROM produtos")]


def buscar_por_id(db, produto_id):
    row = db.execute("SELECT * FROM produtos WHERE id = ?", (produto_id,)).fetchone()
    return _para_dict(row) if row else None


def buscar_por_ids(db, produto_ids):
    """Carrega vários produtos numa única query; devolve {id: produto}."""
    ids = list(dict.fromkeys(produto_ids))
    if not ids:
        return {}
    placeholders = ", ".join("?" for _ in ids)
    rows = db.execute(f"SELECT * FROM produtos WHERE id IN ({placeholders})", ids).fetchall()
    return {row["id"]: _para_dict(row) for row in rows}


def buscar(db, termo="", categoria=None, preco_min=None, preco_max=None):
    clausulas, params = ["1=1"], []
    if termo:
        clausulas.append("(nome LIKE ? OR descricao LIKE ?)")
        params += [f"%{termo}%", f"%{termo}%"]
    if categoria:
        clausulas.append("categoria = ?")
        params.append(categoria)
    if preco_min is not None:
        clausulas.append("preco >= ?")
        params.append(preco_min)
    if preco_max is not None:
        clausulas.append("preco <= ?")
        params.append(preco_max)
    sql = f"SELECT * FROM produtos WHERE {' AND '.join(clausulas)}"
    return [_para_dict(row) for row in db.execute(sql, params)]


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


def remover(db, produto_id):
    db.execute("DELETE FROM produtos WHERE id = ?", (produto_id,))


def baixar_estoque(db, produto_id, quantidade):
    """Baixa condicional: só atualiza se houver estoque. Retorna False se não havia."""
    cursor = db.execute(
        "UPDATE produtos SET estoque = estoque - ? WHERE id = ? AND estoque >= ?",
        (quantidade, produto_id, quantidade),
    )
    return cursor.rowcount == 1

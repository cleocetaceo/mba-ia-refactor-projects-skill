"""Acesso a dados de usuários. A senha (hash) nunca sai deste módulo em listagens."""

TIPO_PADRAO = "cliente"

# Allowlist de campos públicos: senha/hash nunca é serializada.
CAMPOS_PUBLICOS = ("id", "nome", "email", "tipo", "criado_em")
CAMPOS_SESSAO = ("id", "nome", "email", "tipo")


def _to_public_dict(row, campos=CAMPOS_PUBLICOS):
    return {campo: row[campo] for campo in campos}


def listar(db):
    rows = db.execute("SELECT * FROM usuarios ORDER BY id").fetchall()
    return [_to_public_dict(row) for row in rows]


def buscar_por_id(db, usuario_id):
    row = db.execute("SELECT * FROM usuarios WHERE id = ?", (usuario_id,)).fetchone()
    return _to_public_dict(row) if row else None


def existe(db, usuario_id):
    return db.execute("SELECT 1 FROM usuarios WHERE id = ?", (usuario_id,)).fetchone() is not None


def email_cadastrado(db, email):
    return db.execute("SELECT 1 FROM usuarios WHERE email = ?", (email,)).fetchone() is not None


def buscar_credenciais(db, email):
    """Retorna [(dados_de_sessao, hash_da_senha)] para o e-mail informado (uso exclusivo do login)."""
    rows = db.execute("SELECT * FROM usuarios WHERE email = ? ORDER BY id", (email,)).fetchall()
    return [(_to_public_dict(row, CAMPOS_SESSAO), row["senha"]) for row in rows]


def criar(db, nome, email, senha_hash, tipo=TIPO_PADRAO):
    cursor = db.execute(
        "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
        (nome, email, senha_hash, tipo),
    )
    return cursor.lastrowid


def contar(db):
    return db.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0]

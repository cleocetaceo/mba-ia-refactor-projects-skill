"""Acesso a dados de usuários. A senha (hash) nunca sai deste módulo pelas funções públicas."""

TIPO_CLIENTE = "cliente"

# Allowlist de campos expostos pela API.
CAMPOS_PUBLICOS = ("id", "nome", "email", "tipo", "criado_em")
CAMPOS_LOGIN = ("id", "nome", "email", "tipo")


def _publico(row, campos=CAMPOS_PUBLICOS):
    return {campo: row[campo] for campo in campos}


def listar(db):
    return [_publico(row) for row in db.execute("SELECT * FROM usuarios")]


def buscar_por_id(db, usuario_id):
    row = db.execute("SELECT * FROM usuarios WHERE id = ?", (usuario_id,)).fetchone()
    return _publico(row) if row else None


def buscar_credenciais_por_email(db, email):
    """Uso interno da autenticação: devolve as linhas (com hash) que têm o e-mail."""
    return db.execute("SELECT * FROM usuarios WHERE email = ? ORDER BY id", (email,)).fetchall()


def para_login(row):
    return _publico(row, CAMPOS_LOGIN)


def criar(db, nome, email, senha_hash, tipo=TIPO_CLIENTE):
    cursor = db.execute(
        "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
        (nome, email, senha_hash, tipo),
    )
    return cursor.lastrowid

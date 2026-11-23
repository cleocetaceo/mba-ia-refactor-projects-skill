"""Hash de senha forte via werkzeug.security (já incluído no Flask)."""
from werkzeug.security import check_password_hash, generate_password_hash

_PREFIXOS_HASH = ("scrypt:", "pbkdf2:")


def gerar_hash(senha):
    return generate_password_hash(senha)


def eh_hash(valor):
    return isinstance(valor, str) and valor.startswith(_PREFIXOS_HASH) and valor.count("$") == 2


def verificar(senha_hash, senha):
    if not eh_hash(senha_hash):
        return False
    return check_password_hash(senha_hash, senha)

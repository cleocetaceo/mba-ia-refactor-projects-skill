"""Dados de exemplo (mesmos do projeto original) e migração de senhas em texto puro."""
import logging

from src.services import password_service

logger = logging.getLogger(__name__)

PRODUTOS_EXEMPLO = (
    ("Notebook Gamer", "Notebook potente para jogos", 5999.99, 10, "informatica"),
    ("Mouse Wireless", "Mouse sem fio ergonômico", 89.90, 50, "informatica"),
    ("Teclado Mecânico", "Teclado mecânico RGB", 299.90, 30, "informatica"),
    ("Monitor 27''", "Monitor 27 polegadas 144hz", 1899.90, 15, "informatica"),
    ("Headset Gamer", "Headset com microfone", 199.90, 25, "informatica"),
    ("Cadeira Gamer", "Cadeira ergonômica", 1299.90, 8, "moveis"),
    ("Webcam HD", "Webcam 1080p", 249.90, 20, "informatica"),
    ("Hub USB", "Hub USB 3.0 7 portas", 79.90, 40, "informatica"),
    ("SSD 1TB", "SSD NVMe 1TB", 449.90, 35, "informatica"),
    ("Camiseta Dev", "Camiseta estampa código", 59.90, 100, "vestuario"),
)

# Credenciais de desenvolvimento documentadas; as senhas são gravadas com hash.
USUARIOS_EXEMPLO = (
    ("Admin", "admin@loja.com", "admin123", "admin"),
    ("João Silva", "joao@email.com", "123456", "cliente"),
    ("Maria Santos", "maria@email.com", "senha123", "cliente"),
)


def seed_if_empty(db):
    """Popula o banco no boot quando não há produtos (mesma regra do original)."""
    if db.execute("SELECT COUNT(*) FROM produtos").fetchone()[0] != 0:
        return
    with db:
        db.executemany(
            "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) VALUES (?, ?, ?, ?, ?)",
            PRODUTOS_EXEMPLO,
        )
        db.executemany(
            "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
            [(nome, email, password_service.gerar_hash(senha), tipo) for nome, email, senha, tipo in USUARIOS_EXEMPLO],
        )
    logger.info("Banco populado com dados de exemplo")


def migrar_senhas_legadas(db):
    """Converte senhas em texto puro de bancos antigos para hash, preservando o login."""
    legadas = [
        (row["id"], row["senha"])
        for row in db.execute("SELECT id, senha FROM usuarios WHERE senha IS NOT NULL")
        if not password_service.eh_hash(row["senha"])
    ]
    if not legadas:
        return
    with db:
        db.executemany(
            "UPDATE usuarios SET senha = ? WHERE id = ?",
            [(password_service.gerar_hash(senha), usuario_id) for usuario_id, senha in legadas],
        )
    logger.warning("%d senha(s) em texto puro migrada(s) para hash", len(legadas))

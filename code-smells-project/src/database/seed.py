"""Dados de exemplo e migração de senhas legadas (texto puro → hash)."""
import logging

from src.database.connection import transaction
from src.services import password_service

logger = logging.getLogger(__name__)

PRODUTOS_SEED = [
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
]

# Credenciais de exemplo documentadas: gravadas com hash, o login continua igual.
USUARIOS_SEED = [
    ("Admin", "admin@loja.com", "admin123", "admin"),
    ("João Silva", "joao@email.com", "123456", "cliente"),
    ("Maria Santos", "maria@email.com", "senha123", "cliente"),
]


def seed_if_empty(db):
    if db.execute("SELECT COUNT(*) FROM produtos").fetchone()[0] > 0:
        return
    with transaction(db):
        db.executemany(
            "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) VALUES (?, ?, ?, ?, ?)",
            PRODUTOS_SEED,
        )
        db.executemany(
            "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
            [(nome, email, password_service.hash_password(senha), tipo) for nome, email, senha, tipo in USUARIOS_SEED],
        )
    logger.info("Banco populado com dados de exemplo")


def migrate_plaintext_passwords(db):
    """Converte senhas gravadas em texto puro por versões anteriores para hash forte."""
    rows = db.execute("SELECT id, senha FROM usuarios").fetchall()
    legadas = [(row["id"], row["senha"]) for row in rows if not password_service.is_hashed(row["senha"])]
    if not legadas:
        return
    with transaction(db):
        for usuario_id, senha in legadas:
            db.execute(
                "UPDATE usuarios SET senha = ? WHERE id = ?",
                (password_service.hash_password(senha or ""), usuario_id),
            )
    logger.info("%d senha(s) legada(s) migrada(s) para hash", len(legadas))

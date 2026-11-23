"""Validação centralizada de entrada. Mantém as mensagens de erro originais da API."""
import math
import re

from src.middlewares.error_handler import ValidationError
from src.models.pedido_model import STATUS_VALIDOS
from src.models.produto_model import CATEGORIA_PADRAO, CATEGORIAS_VALIDAS, NOME_MAX, NOME_MIN

SENHA_MIN = 6
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
MSG_ITEM_INVALIDO = "Item inválido: produto_id e quantidade (inteiro maior que zero) são obrigatórios"


def _eh_numero(valor):
    return isinstance(valor, (int, float)) and not isinstance(valor, bool) and math.isfinite(valor)


def _como_inteiro(valor, aceitar_texto=False):
    if isinstance(valor, bool):
        return None
    if isinstance(valor, int):
        return valor
    if isinstance(valor, float) and valor.is_integer():
        return int(valor)
    if aceitar_texto and isinstance(valor, str) and valor.strip().isdigit():
        return int(valor.strip())
    return None


def exigir_objeto(dados, mensagem="Dados inválidos"):
    if not dados or not isinstance(dados, dict):
        raise ValidationError(mensagem)
    return dados


def validar_produto(dados):
    """Regras únicas para criar e atualizar produto."""
    exigir_objeto(dados)
    for campo, mensagem in (
        ("nome", "Nome é obrigatório"),
        ("preco", "Preço é obrigatório"),
        ("estoque", "Estoque é obrigatório"),
    ):
        if campo not in dados:
            raise ValidationError(mensagem)

    nome = dados["nome"]
    descricao = dados.get("descricao", "")
    preco = dados["preco"]
    estoque = _como_inteiro(dados["estoque"])
    categoria = dados.get("categoria", CATEGORIA_PADRAO)

    if not _eh_numero(preco):
        raise ValidationError("Preço deve ser numérico")
    if preco < 0:
        raise ValidationError("Preço não pode ser negativo")
    if estoque is None:
        raise ValidationError("Estoque deve ser um número inteiro")
    if estoque < 0:
        raise ValidationError("Estoque não pode ser negativo")
    if not isinstance(nome, str):
        raise ValidationError("Nome deve ser texto")
    if len(nome) < NOME_MIN:
        raise ValidationError("Nome muito curto")
    if len(nome) > NOME_MAX:
        raise ValidationError("Nome muito longo")
    if descricao is None:
        descricao = ""
    if not isinstance(descricao, str):
        raise ValidationError("Descrição deve ser texto")
    if not isinstance(categoria, str) or categoria not in CATEGORIAS_VALIDAS:
        raise ValidationError("Categoria inválida. Válidas: " + str(list(CATEGORIAS_VALIDAS)))

    return {"nome": nome, "descricao": descricao, "preco": preco, "estoque": estoque, "categoria": categoria}


def validar_filtro_preco(valor, nome_parametro):
    if valor is None or valor == "":
        return None
    try:
        numero = float(valor)
    except ValueError:
        raise ValidationError(f"{nome_parametro} deve ser numérico") from None
    if not math.isfinite(numero):
        raise ValidationError(f"{nome_parametro} deve ser numérico")
    return numero


def validar_usuario(dados):
    exigir_objeto(dados)
    nome = dados.get("nome", "")
    email = dados.get("email", "")
    senha = dados.get("senha", "")
    if not nome or not email or not senha:
        raise ValidationError("Nome, email e senha são obrigatórios")
    if not all(isinstance(valor, str) for valor in (nome, email, senha)):
        raise ValidationError("Nome, email e senha devem ser texto")
    if not _EMAIL_RE.match(email):
        raise ValidationError("Email inválido")
    if len(senha) < SENHA_MIN:
        raise ValidationError(f"Senha deve ter pelo menos {SENHA_MIN} caracteres")
    return nome, email, senha


def validar_login(dados):
    if not isinstance(dados, dict):
        dados = {}
    email = dados.get("email", "")
    senha = dados.get("senha", "")
    if not email or not senha or not isinstance(email, str) or not isinstance(senha, str):
        raise ValidationError("Email e senha são obrigatórios")
    return email, senha


def validar_pedido(dados):
    exigir_objeto(dados)
    usuario_id = dados.get("usuario_id")
    itens = dados.get("itens", [])

    if not usuario_id:
        raise ValidationError("Usuario ID é obrigatório")
    usuario_id = _como_inteiro(usuario_id, aceitar_texto=True)
    if usuario_id is None or usuario_id <= 0:
        raise ValidationError("Usuario ID inválido")
    if not itens or not isinstance(itens, list):
        raise ValidationError("Pedido deve ter pelo menos 1 item")

    normalizados = []
    for item in itens:
        if not isinstance(item, dict):
            raise ValidationError(MSG_ITEM_INVALIDO, include_sucesso=True)
        produto_id = _como_inteiro(item.get("produto_id"), aceitar_texto=True)
        quantidade = _como_inteiro(item.get("quantidade"))
        if produto_id is None or quantidade is None or quantidade <= 0:
            raise ValidationError(MSG_ITEM_INVALIDO, include_sucesso=True)
        normalizados.append({"produto_id": produto_id, "quantidade": quantidade})
    return usuario_id, normalizados


def validar_status_pedido(dados):
    novo_status = dados.get("status", "") if isinstance(dados, dict) else ""
    if not isinstance(novo_status, str) or novo_status not in STATUS_VALIDOS:
        raise ValidationError("Status inválido")
    return novo_status

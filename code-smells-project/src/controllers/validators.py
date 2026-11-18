"""Validação de entrada centralizada (mesmas mensagens que a API já devolvia)."""
import math
import re

from src.middlewares.error_handler import ValidationError
from src.models import pedido_model, produto_model

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
SENHA_MIN_LEN = 6

MSG_DADOS_INVALIDOS = "Dados inválidos"


def _is_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _as_int(value):
    """Converte para int aceitando apenas inteiros (ou floats inteiros, ex.: 10.0). Retorna None se inválido."""
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return None


def _non_empty_str(value):
    return isinstance(value, str) and value.strip() != ""


def exigir_objeto(dados):
    if not isinstance(dados, dict) or not dados:
        raise ValidationError(MSG_DADOS_INVALIDOS)
    return dados


def validar_produto(dados):
    """Regras únicas de produto, usadas por criar e atualizar."""
    exigir_objeto(dados)
    if "nome" not in dados:
        raise ValidationError("Nome é obrigatório")
    if "preco" not in dados:
        raise ValidationError("Preço é obrigatório")
    if "estoque" not in dados:
        raise ValidationError("Estoque é obrigatório")

    nome = dados["nome"]
    descricao = dados.get("descricao", "")
    preco = dados["preco"]
    estoque = _as_int(dados["estoque"])
    categoria = dados.get("categoria", produto_model.CATEGORIA_PADRAO)

    if not isinstance(nome, str):
        raise ValidationError("Nome deve ser um texto")
    if not isinstance(descricao, str):
        raise ValidationError("Descrição deve ser um texto")
    if not _is_number(preco):
        raise ValidationError("Preço deve ser um número")
    if estoque is None:
        raise ValidationError("Estoque deve ser um número inteiro")
    if preco < 0:
        raise ValidationError("Preço não pode ser negativo")
    if estoque < 0:
        raise ValidationError("Estoque não pode ser negativo")
    if len(nome) < produto_model.NOME_MIN_LEN:
        raise ValidationError("Nome muito curto")
    if len(nome) > produto_model.NOME_MAX_LEN:
        raise ValidationError("Nome muito longo")
    if categoria not in produto_model.CATEGORIAS_VALIDAS:
        raise ValidationError("Categoria inválida. Válidas: " + str(list(produto_model.CATEGORIAS_VALIDAS)))

    return {"nome": nome, "descricao": descricao, "preco": preco, "estoque": estoque, "categoria": categoria}


def validar_filtro_preco(valor, campo):
    if not valor:
        return None
    try:
        numero = float(valor)
    except (TypeError, ValueError):
        raise ValidationError(f"{campo} deve ser numérico") from None
    if not math.isfinite(numero):
        raise ValidationError(f"{campo} deve ser numérico")
    return numero


def validar_novo_usuario(dados):
    exigir_objeto(dados)
    nome, email, senha = dados.get("nome", ""), dados.get("email", ""), dados.get("senha", "")
    if not (_non_empty_str(nome) and _non_empty_str(email) and _non_empty_str(senha)):
        raise ValidationError("Nome, email e senha são obrigatórios")
    email = email.strip()
    if not EMAIL_REGEX.match(email):
        raise ValidationError("Email inválido")
    if len(senha) < SENHA_MIN_LEN:
        raise ValidationError(f"Senha deve ter pelo menos {SENHA_MIN_LEN} caracteres")
    return {"nome": nome.strip(), "email": email, "senha": senha}


def validar_login(dados):
    dados = dados if isinstance(dados, dict) else {}
    email, senha = dados.get("email", ""), dados.get("senha", "")
    if not (_non_empty_str(email) and _non_empty_str(senha)):
        raise ValidationError("Email e senha são obrigatórios")
    return email.strip(), senha


def validar_pedido(dados):
    exigir_objeto(dados)
    usuario_id = dados.get("usuario_id")
    itens = dados.get("itens", [])

    if not usuario_id:
        raise ValidationError("Usuario ID é obrigatório")
    usuario_id = _as_int(usuario_id)
    if usuario_id is None or usuario_id <= 0:
        raise ValidationError("Usuario ID inválido")
    if not isinstance(itens, list) or len(itens) == 0:
        raise ValidationError("Pedido deve ter pelo menos 1 item")

    itens_validos = []
    for item in itens:
        produto_id = _as_int(item.get("produto_id")) if isinstance(item, dict) else None
        quantidade = _as_int(item.get("quantidade")) if isinstance(item, dict) else None
        if produto_id is None or produto_id <= 0 or quantidade is None or quantidade <= 0:
            raise ValidationError("Item inválido: produto_id e quantidade (inteiro maior que zero) são obrigatórios")
        itens_validos.append({"produto_id": produto_id, "quantidade": quantidade})

    return usuario_id, itens_validos


def validar_status(dados):
    status = dados.get("status", "") if isinstance(dados, dict) else ""
    if status not in pedido_model.STATUS_VALIDOS:
        raise ValidationError("Status inválido")
    return status

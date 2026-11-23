"""Notificações de pedido (e-mail, SMS, push).

Ainda não há integração real: os envios são registrados em log, como o projeto
original fazia com print. Trocar por um provedor real só exige mudar este módulo.
"""
import logging

logger = logging.getLogger(__name__)


def pedido_criado(pedido_id, usuario_id):
    logger.info("ENVIANDO EMAIL: Pedido %s criado para usuario %s", pedido_id, usuario_id)
    logger.info("ENVIANDO SMS: Seu pedido foi recebido!")
    logger.info("ENVIANDO PUSH: Novo pedido recebido pelo sistema")


def pedido_aprovado(pedido_id):
    logger.info("NOTIFICAÇÃO: Pedido %s foi aprovado! Preparar envio.", pedido_id)


def pedido_cancelado(pedido_id):
    logger.info("NOTIFICAÇÃO: Pedido %s cancelado. Devolver estoque.", pedido_id)

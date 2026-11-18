const { PAYMENT_STATUS } = require('../models/payment.model');

// Gateway simulado: cartões que começam com este prefixo são aprovados (regra original).
const APPROVED_CARD_PREFIX = '4';
const VISIBLE_CARD_DIGITS = 4;

const maskCard = (cardNumber) => `**** ${cardNumber.slice(-VISIBLE_CARD_DIGITS)}`;

function createPaymentService({ gatewayKey, logger }) {
    if (!gatewayKey) {
        logger.warn('PAYMENT_GATEWAY_KEY não definida: usando o gateway de pagamento simulado');
    }

    return {
        /** Autoriza a cobrança e devolve o status do pagamento (PAID | DENIED). */
        authorize(cardNumber, amount) {
            const status = cardNumber.startsWith(APPROVED_CARD_PREFIX)
                ? PAYMENT_STATUS.PAID
                : PAYMENT_STATUS.DENIED;
            logger.info(`Pagamento de ${amount} no cartão ${maskCard(cardNumber)}: ${status}`);
            return status;
        },
    };
}

module.exports = { createPaymentService };

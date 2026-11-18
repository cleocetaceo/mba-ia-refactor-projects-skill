const { ValidationError } = require('../utils/errors');

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const CARD_SEPARATORS = /[\s-]/g;
const CARD_MIN_DIGITS = 12;
const CARD_MAX_DIGITS = 19;
const CARD_PATTERN = new RegExp(`^\\d{${CARD_MIN_DIGITS},${CARD_MAX_DIGITS}}$`);

const isNonEmptyString = (value) => typeof value === 'string' && value.trim() !== '';

/** Aceita inteiro positivo como number ou string numérica ("2"); devolve null se inválido. */
function parsePositiveInt(value) {
    const number = typeof value === 'string' && value.trim() !== '' ? Number(value) : value;
    return Number.isInteger(number) && number > 0 ? number : null;
}

/**
 * Valida o payload público do checkout. Os nomes do contrato (usr, eml, pwd, c_id, card)
 * são mantidos e convertidos para nomes internos claros.
 */
function validateCheckoutInput(body) {
    const { usr, eml, pwd, c_id: rawCourseId, card } = body || {};

    if (!isNonEmptyString(usr) || !isNonEmptyString(eml) || !isNonEmptyString(card)) {
        throw new ValidationError();
    }

    const email = eml.trim();
    if (!EMAIL_PATTERN.test(email)) throw new ValidationError();

    const cardNumber = card.replace(CARD_SEPARATORS, '');
    if (!CARD_PATTERN.test(cardNumber)) throw new ValidationError();

    const courseId = parsePositiveInt(rawCourseId);
    if (courseId === null) throw new ValidationError();

    if (pwd !== undefined && pwd !== null && typeof pwd !== 'string') throw new ValidationError();

    return {
        name: usr.trim(),
        email,
        password: pwd || '',
        courseId,
        cardNumber,
    };
}

function validateId(rawId) {
    const id = parsePositiveInt(rawId);
    if (id === null) throw new ValidationError();
    return id;
}

module.exports = { validateCheckoutInput, validateId };

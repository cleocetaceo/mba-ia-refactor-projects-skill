const http = require('node:http');
const { AppError } = require('../utils/errors');

const CLIENT_ERROR_MIN = 400;
const SERVER_ERROR_MIN = 500;

/**
 * Handler central de erros (registrado por último). Mantém o formato original da API:
 * erros respondem texto puro. Detalhes de erros inesperados vão só para o log.
 */
module.exports = (logger) => (err, req, res, next) => {
    if (res.headersSent) return next(err);

    if (err instanceof AppError) {
        return res.status(err.statusCode).send(err.message);
    }

    // Erros de cliente do próprio Express/body-parser (ex.: JSON malformado).
    const status = err.status || err.statusCode;
    if (Number.isInteger(status) && status >= CLIENT_ERROR_MIN && status < SERVER_ERROR_MIN) {
        return res.status(status).send(http.STATUS_CODES[status]);
    }

    logger.error(`Erro inesperado em ${req.method} ${req.originalUrl}`, err);
    return res.status(SERVER_ERROR_MIN).send('Erro interno do servidor');
};

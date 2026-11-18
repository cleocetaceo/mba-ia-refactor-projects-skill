// Express 4 não captura rejeições de handlers async: encaminha o erro para o errorHandler central.
module.exports = (handler) => (req, res, next) => {
    Promise.resolve(handler(req, res, next)).catch(next);
};

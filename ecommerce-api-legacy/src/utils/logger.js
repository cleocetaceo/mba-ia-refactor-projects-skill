// Logger mínimo com nível e timestamp. Nunca registre senha, cartão completo ou chaves.
const timestamp = () => new Date().toISOString();

module.exports = {
    info: (message) => console.log(`[INFO] ${timestamp()} ${message}`),
    warn: (message) => console.warn(`[WARN] ${timestamp()} ${message}`),
    error: (message, err) => console.error(`[ERROR] ${timestamp()} ${message}`, err || ''),
};

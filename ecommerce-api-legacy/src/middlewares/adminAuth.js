const crypto = require('node:crypto');

const ADMIN_TOKEN_HEADER = 'X-Admin-Token';

// Compara digests de tamanho fixo para não vazar o tamanho do token nem depender de timing.
const digest = (value) => crypto.createHash('sha256').update(value).digest();

/**
 * Exige o header X-Admin-Token igual a ADMIN_TOKEN.
 * Sem ADMIN_TOKEN configurado → 403 (endpoint desabilitado); token ausente/inválido → 401.
 */
module.exports = (adminToken) => {
    const expected = adminToken ? digest(adminToken) : null;

    return (req, res, next) => {
        if (!expected) return res.status(403).send('Endpoint administrativo desabilitado');

        const provided = digest(req.get(ADMIN_TOKEN_HEADER) || '');
        if (!crypto.timingSafeEqual(provided, expected)) {
            return res.status(401).send('Não autorizado');
        }
        next();
    };
};

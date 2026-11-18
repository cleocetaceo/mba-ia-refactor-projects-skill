const crypto = require('node:crypto');
const { promisify } = require('node:util');

const scrypt = promisify(crypto.scrypt);

const SALT_BYTES = 16;
const KEY_LENGTH = 64;
const HASH_PREFIX = 'scrypt';

// Formato armazenado: "scrypt$<salt hex>$<hash hex>".
async function hashPassword(plain) {
    const salt = crypto.randomBytes(SALT_BYTES).toString('hex');
    const derived = await scrypt(plain, salt, KEY_LENGTH);
    return `${HASH_PREFIX}$${salt}$${derived.toString('hex')}`;
}

async function verifyPassword(plain, stored) {
    const [prefix, salt, hash] = String(stored).split('$');
    if (prefix !== HASH_PREFIX || !salt || !hash) return false;
    const expected = Buffer.from(hash, 'hex');
    const candidate = await scrypt(plain, salt, expected.length);
    return crypto.timingSafeEqual(candidate, expected);
}

module.exports = { hashPassword, verifyPassword };

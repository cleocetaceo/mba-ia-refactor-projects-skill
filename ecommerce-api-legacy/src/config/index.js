// Configuração centralizada: todo valor vem do ambiente, com defaults seguros para desenvolvimento.

// Carrega um arquivo .env opcional da raiz do projeto (API nativa do Node >= 20.12, sem dependência extra).
if (typeof process.loadEnvFile === 'function') {
    try {
        process.loadEnvFile();
    } catch (err) {
        if (err.code !== 'ENOENT') throw err;
    }
}

const DEFAULT_PORT = 3000;

module.exports = Object.freeze({
    port: Number(process.env.PORT) || DEFAULT_PORT,
    // Vazio = escuta em todas as interfaces, como no código original.
    host: process.env.HOST || undefined,
    // ':memory:' mantém o comportamento original (banco volátil recriado a cada boot).
    databasePath: process.env.DATABASE_PATH || ':memory:',
    paymentGatewayKey: process.env.PAYMENT_GATEWAY_KEY || '',
    // Sem ADMIN_TOKEN os endpoints administrativos ficam desabilitados (403).
    adminToken: process.env.ADMIN_TOKEN || '',
});

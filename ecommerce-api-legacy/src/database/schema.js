const { PAYMENT_STATUS } = require('../models/payment.model');

const SCHEMA = `
    CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT, email TEXT, pass TEXT);
    CREATE TABLE IF NOT EXISTS courses (id INTEGER PRIMARY KEY, title TEXT, price REAL, active INTEGER);
    CREATE TABLE IF NOT EXISTS enrollments (id INTEGER PRIMARY KEY, user_id INTEGER, course_id INTEGER);
    CREATE TABLE IF NOT EXISTS payments (id INTEGER PRIMARY KEY, enrollment_id INTEGER, amount REAL, status TEXT);
    CREATE TABLE IF NOT EXISTS audit_logs (id INTEGER PRIMARY KEY, action TEXT, created_at DATETIME);
`;

// Mesmos dados de exemplo do código original; a senha do seed ('123') agora é gravada com hash scrypt.
const SEED_USER = { name: 'Leonan', email: 'leonan@fullcycle.com.br', password: '123' };

/** Cria as tabelas e, se o banco estiver vazio, carrega o seed. Executado no boot, antes do listen. */
async function initSchema(db, { hashPassword }) {
    await db.exec(SCHEMA);

    // Cursos nunca são apagados pela API: se já existem, o seed já foi aplicado (DATABASE_PATH persistente).
    const { total } = await db.get('SELECT COUNT(*) AS total FROM courses');
    if (total > 0) return;

    const seedPasswordHash = await hashPassword(SEED_USER.password);
    await db.transaction(async () => {
        await db.run(
            'INSERT INTO users (name, email, pass) VALUES (?, ?, ?)',
            [SEED_USER.name, SEED_USER.email, seedPasswordHash],
        );
        await db.run(
            "INSERT INTO courses (title, price, active) VALUES ('Clean Architecture', 997.00, 1), ('Docker', 497.00, 1)",
        );
        await db.run('INSERT INTO enrollments (user_id, course_id) VALUES (1, 1)');
        await db.run(
            'INSERT INTO payments (enrollment_id, amount, status) VALUES (1, 997.00, ?)',
            [PAYMENT_STATUS.PAID],
        );
    });
}

module.exports = { initSchema };

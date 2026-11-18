const sqlite3 = require('sqlite3');

/**
 * Abre o banco SQLite e expõe helpers baseados em Promise.
 * A conexão é criada pelo composition root (src/app.js) e injetada nos models.
 */
function createConnection(filename) {
    const db = new sqlite3.Database(filename);

    const run = (sql, params = []) => new Promise((resolve, reject) => {
        db.run(sql, params, function onRun(err) {
            if (err) return reject(err);
            resolve({ lastID: this.lastID, changes: this.changes });
        });
    });

    const get = (sql, params = []) => new Promise((resolve, reject) => {
        db.get(sql, params, (err, row) => (err ? reject(err) : resolve(row)));
    });

    const all = (sql, params = []) => new Promise((resolve, reject) => {
        db.all(sql, params, (err, rows) => (err ? reject(err) : resolve(rows)));
    });

    const exec = (sql) => new Promise((resolve, reject) => {
        db.exec(sql, (err) => (err ? reject(err) : resolve()));
    });

    const close = () => new Promise((resolve, reject) => {
        db.close((err) => (err ? reject(err) : resolve()));
    });

    // Transações são enfileiradas: a conexão é única, então duas transações
    // concorrentes não podem se intercalar (BEGIN dentro de BEGIN).
    let pendingTransactions = Promise.resolve();

    function transaction(work) {
        const result = pendingTransactions.then(async () => {
            await run('BEGIN IMMEDIATE');
            try {
                const value = await work();
                await run('COMMIT');
                return value;
            } catch (err) {
                await run('ROLLBACK').catch(() => {});
                throw err;
            }
        });
        pendingTransactions = result.catch(() => {});
        return result;
    }

    return { run, get, all, exec, close, transaction };
}

module.exports = { createConnection };

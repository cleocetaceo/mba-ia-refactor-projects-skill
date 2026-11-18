// Composition root: carrega config, inicializa o banco, injeta dependências, registra rotas e sobe o servidor.
const express = require('express');

const config = require('./config');
const logger = require('./utils/logger');
const { createConnection } = require('./database/connection');
const { initSchema } = require('./database/schema');

const { createUserModel } = require('./models/user.model');
const { createCourseModel } = require('./models/course.model');
const { createEnrollmentModel } = require('./models/enrollment.model');
const { createPaymentModel } = require('./models/payment.model');
const { createAuditLogModel } = require('./models/auditLog.model');

const passwordService = require('./services/password.service');
const { createPaymentService } = require('./services/payment.service');

const { createCheckoutController } = require('./controllers/checkout.controller');
const { createReportController } = require('./controllers/report.controller');
const { createUserController } = require('./controllers/user.controller');

const createAdminAuth = require('./middlewares/adminAuth');
const createErrorHandler = require('./middlewares/errorHandler');
const createApiRouter = require('./routes');

function buildApp(db) {
    const models = {
        userModel: createUserModel(db),
        courseModel: createCourseModel(db),
        enrollmentModel: createEnrollmentModel(db),
        paymentModel: createPaymentModel(db),
        auditLogModel: createAuditLogModel(db),
    };
    const paymentService = createPaymentService({ gatewayKey: config.paymentGatewayKey, logger });

    const controllers = {
        checkout: createCheckoutController({
            ...models,
            transaction: db.transaction,
            paymentService,
            passwordService,
            logger,
        }),
        report: createReportController({ courseModel: models.courseModel }),
        user: createUserController({ ...models, transaction: db.transaction }),
    };

    const app = express();
    app.use(express.json());
    app.use('/api', createApiRouter({ controllers, requireAdmin: createAdminAuth(config.adminToken) }));
    app.use(createErrorHandler(logger));
    return app;
}

async function start() {
    const db = createConnection(config.databasePath);
    await initSchema(db, passwordService);

    if (!config.adminToken) {
        logger.warn('ADMIN_TOKEN não definido: endpoints administrativos respondem 403');
    }

    const app = buildApp(db);
    const onListening = () => logger.info(`LMS API rodando na porta ${config.port}...`);
    const server = config.host
        ? app.listen(config.port, config.host, onListening)
        : app.listen(config.port, onListening);

    server.on('error', (err) => {
        logger.error(`Não foi possível escutar na porta ${config.port}`, err);
        process.exit(1);
    });
}

start().catch((err) => {
    logger.error('Falha ao iniciar a aplicação', err);
    process.exit(1);
});

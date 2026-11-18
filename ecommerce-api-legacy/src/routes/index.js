const express = require('express');
const checkoutRoutes = require('./checkout.routes');
const reportRoutes = require('./report.routes');
const userRoutes = require('./user.routes');

/** Router da API, montado em /api pelo composition root. */
module.exports = ({ controllers, requireAdmin }) => {
    const router = express.Router();

    router.use(checkoutRoutes(controllers.checkout));
    router.use(reportRoutes(controllers.report, requireAdmin));
    router.use(userRoutes(controllers.user, requireAdmin));

    return router;
};

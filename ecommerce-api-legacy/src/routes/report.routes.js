const express = require('express');
const asyncHandler = require('../utils/asyncHandler');

module.exports = (reportController, requireAdmin) => {
    const router = express.Router();

    router.get('/admin/financial-report', requireAdmin, asyncHandler(async (req, res) => {
        res.json(await reportController.financialReport());
    }));

    return router;
};

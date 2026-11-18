const express = require('express');
const asyncHandler = require('../utils/asyncHandler');

module.exports = (checkoutController) => {
    const router = express.Router();

    router.post('/checkout', asyncHandler(async (req, res) => {
        const result = await checkoutController.checkout(req.body);
        res.status(200).json(result);
    }));

    return router;
};

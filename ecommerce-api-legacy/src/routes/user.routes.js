const express = require('express');
const asyncHandler = require('../utils/asyncHandler');

const USER_DELETED_MESSAGE = 'Usuário deletado, junto com suas matrículas e pagamentos.';

module.exports = (userController, requireAdmin) => {
    const router = express.Router();

    router.delete('/users/:id', requireAdmin, asyncHandler(async (req, res) => {
        await userController.deleteUser(req.params.id);
        res.send(USER_DELETED_MESSAGE);
    }));

    return router;
};

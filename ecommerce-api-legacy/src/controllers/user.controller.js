const { validateId } = require('./validators');

function createUserController({ transaction, userModel, enrollmentModel, paymentModel, auditLogModel }) {
    return {
        /** Remove o usuário e seus dependentes (pagamentos e matrículas) na mesma transação. */
        async deleteUser(rawId) {
            const userId = validateId(rawId);
            await transaction(async () => {
                await paymentModel.deleteByUserId(userId);
                await enrollmentModel.deleteByUserId(userId);
                await userModel.deleteById(userId);
                await auditLogModel.log(`Usuário ${userId} removido`);
            });
        },
    };
}

module.exports = { createUserController };

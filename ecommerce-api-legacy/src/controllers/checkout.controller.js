const { PAYMENT_STATUS } = require('../models/payment.model');
const { NotFoundError, ValidationError, PaymentDeclinedError } = require('../utils/errors');
const { validateCheckoutInput } = require('./validators');

function createCheckoutController({
    transaction,
    userModel,
    courseModel,
    enrollmentModel,
    paymentModel,
    auditLogModel,
    paymentService,
    passwordService,
    logger,
}) {
    return {
        /**
         * Caso de uso de checkout: valida, autoriza o pagamento e só então grava
         * usuário (se novo) + matrícula + pagamento + auditoria numa única transação.
         */
        async checkout(body) {
            const { name, email, password, courseId, cardNumber } = validateCheckoutInput(body);

            const course = await courseModel.findActiveById(courseId);
            if (!course) throw new NotFoundError('Curso não encontrado');

            const existingUser = await userModel.findByEmail(email);
            // Usuário novo precisa informar senha: não existe mais senha padrão.
            if (!existingUser && !password) throw new ValidationError();

            const paymentStatus = paymentService.authorize(cardNumber, course.price);
            if (paymentStatus !== PAYMENT_STATUS.PAID) throw new PaymentDeclinedError();

            const passwordHash = existingUser ? null : await passwordService.hashPassword(password);

            const { userId, enrollmentId } = await transaction(async () => {
                const buyerId = existingUser
                    ? existingUser.id
                    : await userModel.create({ name, email, passwordHash });
                const newEnrollmentId = await enrollmentModel.create(buyerId, course.id);
                await paymentModel.create(newEnrollmentId, course.price, paymentStatus);
                await auditLogModel.log(`Checkout curso ${course.id} por ${buyerId}`);
                return { userId: buyerId, enrollmentId: newEnrollmentId };
            });

            logger.info(`Checkout concluído: curso ${course.id}, usuário ${userId}, matrícula ${enrollmentId}`);
            return { msg: 'Sucesso', enrollment_id: enrollmentId };
        },
    };
}

module.exports = { createCheckoutController };

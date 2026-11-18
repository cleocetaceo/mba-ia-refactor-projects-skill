const { PAYMENT_STATUS } = require('../models/payment.model');

const UNKNOWN_STUDENT = 'Unknown';

function createReportController({ courseModel }) {
    return {
        /** Receita por curso (apenas pagamentos PAID) e lista de alunos com o valor pago. */
        async financialReport() {
            const rows = await courseModel.listEnrollmentsWithPayments();
            const reportByCourse = new Map();

            for (const row of rows) {
                let courseReport = reportByCourse.get(row.course_id);
                if (!courseReport) {
                    courseReport = { course: row.course_title, revenue: 0, students: [] };
                    reportByCourse.set(row.course_id, courseReport);
                }

                if (row.enrollment_id === null) continue;

                if (row.payment_status === PAYMENT_STATUS.PAID) {
                    courseReport.revenue += row.payment_amount;
                }
                courseReport.students.push({
                    student: row.student_name ?? UNKNOWN_STUDENT,
                    paid: row.payment_amount ?? 0,
                });
            }

            return [...reportByCourse.values()];
        },
    };
}

module.exports = { createReportController };

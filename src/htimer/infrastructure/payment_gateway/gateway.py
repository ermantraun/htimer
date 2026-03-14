import asyncio  # type: ignore
from uuid import UUID

from yookassa import Configuration, Refund  # type: ignore
from yookassa import Payment as YooKassaPayment

from htimer.application import common_exceptions, common_interfaces
from htimer.config import Config
from htimer.domain.entities import Payment, Project, User  # type: ignore


class YooKassaGateway(common_interfaces.PaymentGateway):
    def __init__(self, config: Config):
        Configuration.account_id = config.yookassa.shop_id
        Configuration.secret_key = config.yookassa.secret_key
        self.host_name = config.host_info.host_name
        self.confirmation_uri = config.yookassa.confirmation_uri
        self.http_secure = config.host_info.http_secure
        self.confirmation_url = f"{'https' if self.http_secure else 'http'}://{self.host_name}{self.confirmation_uri}"

    async def create_payment(
        self, actor: User, project: Project, amount: float, payment: Payment
    ) -> tuple[str, UUID] | common_exceptions.PaymentFailedError:

        def _create_payment():

            yookassa_payment = YooKassaPayment.create(
                {  # type: ignore
                    "amount": {"value": f"{amount:.2f}", "currency": "RUB"},
                    "receipt": {
                        "customer": {"full_name": actor.name, "email": actor.email},
                        "items": [
                            {
                                "description": f"Subscription payment for project {project.name}",
                                "quantity": 1,
                                "amount": {"value": f"{amount:.2f}", "currency": "RUB"},
                            }
                        ],
                        "vat_code": 11,
                    },
                    "description": f"Subscription payment for project {project.name} by user {actor.name}",
                    "metadata": {"payment_uuid": str(payment.uuid)},
                    "capture": True,
                    "confirmation": {
                        "type": "redirect",
                        "return_url": self.confirmation_url,
                    },
                },
                idempotency_key=str(payment.uuid),
            )

            confirmation = yookassa_payment.confirmation
            if (
                confirmation is None
                or getattr(confirmation, "confirmation_url", None) is None
            ):
                raise common_exceptions.PaymentFailedError(
                    "Ошибка платёжного шлюза: отсутствует ссылка подтверждения."
                )

            payment_id = getattr(yookassa_payment, "id", None)
            if not isinstance(payment_id, str) or not payment_id:
                raise common_exceptions.PaymentFailedError(
                    "Ошибка платёжного шлюза: отсутствует идентификатор платежа."
                )

            try:
                payment_uuid = UUID(payment_id)
            except ValueError:
                raise common_exceptions.PaymentFailedError(
                    "Ошибка платёжного шлюза: некорректный идентификатор платежа."
                )

            return (confirmation.confirmation_url, payment_uuid)

        return await asyncio.to_thread(_create_payment)

    async def verify_payment_complete(
        self, id_: str
    ) -> bool | common_exceptions.PaymentNotExistsError:

        def _verify_payment_complete():
            try:
                yookassa_payment = YooKassaPayment.find_one(id_)  # type: ignore
            except Exception:
                raise common_exceptions.PaymentFailedError(
                    "Ошибка платёжного шлюза: не удалось проверить статус платежа."
                )

            return getattr(yookassa_payment, "status", None) == "succeeded"

        return await asyncio.to_thread(_verify_payment_complete)

    async def refund_payment(
        self, payment: Payment, gateway_payment_id: str
    ) -> (
        bool
        | common_exceptions.PaymentRefundFailedError
        | common_exceptions.PaymentNotExistsError
    ):

        def _refund_payment():

            refund = Refund.create(
                {  # type: ignore
                    "amount": {
                        "value": f"{payment.amount.amount:.2f}",
                        "currency": "RUB",
                    },
                    "payment_id": gateway_payment_id,
                },
                idempotency_key=str(payment.uuid),
            )

            status = getattr(refund, "status", None)

            if status != "succeeded":
                return common_exceptions.PaymentRefundFailedError(
                    f"Ошибка возврата платежа: статус {status}."
                )

            return True

        return await asyncio.to_thread(_refund_payment)

from datetime import timedelta
from typing import Any
from uuid import UUID, uuid4

from htimer.application import common_exceptions, common_interfaces
from htimer.domain import entities

from . import dto, exceptions, interfaces


class CreateSubscriptionInteractor:
    def __init__(
        self,
        subscription_repository: common_interfaces.SubscriptionRepository,
        user_repository: common_interfaces.UserRepository,
        project_repository: common_interfaces.ProjectRepository,
        context: common_interfaces.Context,
        clock: common_interfaces.Clock,
        authorization_policy: interfaces.SubscriptionAuthorizationPolicy,
        session: common_interfaces.DBSession,
    ):
        self.subscription_repository = subscription_repository
        self.user_repository = user_repository
        self.context = context
        self.clock = clock
        self.authorization_policy = authorization_policy
        self.project_repository = project_repository
        self.session = session

    async def execute(
        self, data: dto.CreateSubscriptionInDTO
    ) -> dto.CreateSubscriptionOutDTO:
        """Создаёт подписку проекта.

        Args:
            data: Структура CreateSubscriptionInDTO.
                - project_uuid: UUID

        Returns:
            dto.CreateSubscriptionOutDTO: Структура результата.
                - subscription: entities.Subscription

        Raises:
            common_exceptions.InvalidTokenError: Токен пользователя невалиден.
            common_exceptions.UserNotFoundError: Пользователь не найден.
            common_exceptions.ProjectNotFoundError: Проект не найден.
            exceptions.SubscriptionAuthorizationError: Недостаточно прав для создания подписки.
            exceptions.CantCreateSubscription: Нарушены доменные ограничения создания подписки.
            common_exceptions.SubscriptionAlreadyExistsError: Подписка уже существует.
            common_exceptions.RepositoryError: Ошибка репозитория.
        """
        actor_uuid = self.context.get_current_user_uuid()
        if isinstance(actor_uuid, common_exceptions.InvalidTokenError):
            raise actor_uuid

        actor = await self.user_repository.get_by_uuid(actor_uuid)
        if isinstance(
            actor,
            (common_exceptions.UserNotFoundError, common_exceptions.RepositoryError),
        ):
            raise actor

        project = await self.project_repository.get_by_uuid(data.project_uuid)
        if isinstance(
            project,
            (common_exceptions.ProjectNotFoundError, common_exceptions.RepositoryError),
        ):
            raise project

        authorization_error = self.authorization_policy.decide_create_subscription(
            actor=actor,
            project=project,
        )
        if authorization_error is not None:
            raise authorization_error

        new_subscription = entities.Subscription(
            uuid=uuid4(),
            project=project,
            created_at=await self.clock.now_date(),
        )

        ensure_err = new_subscription.ensure_create()
        if ensure_err:
            raise exceptions.CantCreateSubscription(ensure_err)

        created_subscription = await self.subscription_repository.create(
            new_subscription
        )
        if isinstance(
            created_subscription,
            (
                common_exceptions.SubscriptionAlreadyExistsError,
                common_exceptions.ProjectNotFoundError,
                common_exceptions.RepositoryError,
            ),
        ):
            raise created_subscription
        await self.session.commit()
        return dto.CreateSubscriptionOutDTO(created_subscription)


class UpdateSubscriptionInteractor:
    def __init__(
        self,
        session: common_interfaces.DBSession,
        subscription_repository: common_interfaces.SubscriptionRepository,
        user_repository: common_interfaces.UserRepository,
        project_repository: common_interfaces.ProjectRepository,
        context: common_interfaces.Context,
        clock: common_interfaces.Clock,
        authorization_policy: interfaces.SubscriptionAuthorizationPolicy,
    ):
        self.subscription_repository = subscription_repository
        self.user_repository = user_repository
        self.project_repository = project_repository
        self.context = context
        self.clock = clock
        self.authorization_policy = authorization_policy
        self.session = session

    async def execute(self, data: dto.UpdateSubscriptionInDTO) -> None:
        """Обновляет состояние подписки проекта.

        Args:
            data: Структура UpdateSubscriptionInDTO.
                - project_uuid: UUID
                - auto_renew: bool | None
                - status: str | None

        Returns:
            None: Подписка успешно обновлена.

        Raises:
            common_exceptions.InvalidTokenError: Токен пользователя невалиден.
            common_exceptions.UserNotFoundError: Пользователь не найден.
            common_exceptions.ProjectNotFoundError: Проект не найден.
            common_exceptions.SubscriptionNotFoundError: Подписка не найдена.
            exceptions.SubscriptionAuthorizationError: Недостаточно прав для обновления подписки.
            exceptions.CantUpdateSubscription: Нарушены доменные ограничения обновления подписки.
            common_exceptions.RepositoryError: Ошибка репозитория.
        """

        actor_uuid = self.context.get_current_user_uuid()
        if isinstance(actor_uuid, common_exceptions.InvalidTokenError):
            raise actor_uuid

        actor = await self.user_repository.get_by_uuid(actor_uuid)
        if isinstance(
            actor,
            (common_exceptions.UserNotFoundError, common_exceptions.RepositoryError),
        ):
            raise actor

        project = await self.project_repository.get_by_uuid(data.project_uuid)
        if isinstance(
            project,
            (common_exceptions.ProjectNotFoundError, common_exceptions.RepositoryError),
        ):
            raise project

        auth_err = self.authorization_policy.decide_update_subscription(
            actor=actor, project=project
        )
        if auth_err is not None:
            raise auth_err

        subscription = await self.project_repository.get_current_subscription(
            data.project_uuid
        )
        if isinstance(
            subscription,
            (
                common_exceptions.SubscriptionNotFoundError,
                common_exceptions.ProjectNotFoundError,
                common_exceptions.RepositoryError,
            ),
        ):
            raise subscription

        ensure_err = subscription.ensure_update(
            entities.SubscriptionStatus(data.status)
        )

        if ensure_err:
            raise exceptions.CantUpdateSubscription(ensure_err)

        update_result = await self.subscription_repository.update(
            subscription_uuid=subscription.uuid,
            data={
                "status": entities.SubscriptionStatus.CANCELLED,
                "auto_renew": data.auto_renew,
                "end_date": None,
            },
        )

        if isinstance(
            update_result,
            (
                common_exceptions.SubscriptionNotFoundError,
                common_exceptions.RepositoryError,
            ),
        ):
            raise update_result

        await self.session.commit()

        return


class ExtendSubscriptionInteractor:
    def __init__(
        self,
        subscription_repository: common_interfaces.SubscriptionRepository,
        project_repository: common_interfaces.ProjectRepository,
        payment_repository: common_interfaces.PaymentRepository,
        payment_gateway: common_interfaces.PaymentGateway,
        clock: common_interfaces.Clock,
        session: common_interfaces.DBSession,
    ):
        self.subscription_repository = subscription_repository
        self.project_repository = project_repository
        self.clock = clock
        self.payment_repository = payment_repository
        self.payment_gateway = payment_gateway
        self.session = session

    async def execute(self, data: dto.ExtendSubscriptionInDTO) -> None:
        """Продлевает активную подписку по завершённому платежу.

        Args:
            data: Структура ExtendSubscriptionInDTO.
                - project_uuid: UUID
                - payment_uuid: UUID

        Returns:
            None: Подписка успешно продлена.

        Raises:
            common_exceptions.ProjectNotFoundError: Проект не найден.
            common_exceptions.SubscriptionNotFoundError: Подписка не найдена.
            common_exceptions.PaymentNotFoundError: Платёж не найден.
            common_exceptions.PaymentNotComplete: Платёж не завершён.
            common_exceptions.PaymentNotExistsError: Платёж отсутствует в платёжном шлюзе.
            exceptions.CantExtendSubscription: Продление подписки невозможно.
            common_exceptions.RepositoryError: Ошибка репозитория.
        """

        project = await self.project_repository.get_by_uuid(data.project_uuid)
        if isinstance(
            project,
            (common_exceptions.ProjectNotFoundError, common_exceptions.RepositoryError),
        ):
            raise project

        subscription = await self.subscription_repository.get_by_project_uuid(
            data.project_uuid, lock_record=True
        )
        if isinstance(
            subscription,
            (
                common_exceptions.SubscriptionNotFoundError,
                common_exceptions.ProjectNotFoundError,
                common_exceptions.RepositoryError,
            ),
        ):
            raise subscription

        payment = await self.payment_repository.get_by_uuid(data.payment_uuid)

        if isinstance(
            payment,
            (common_exceptions.PaymentNotFoundError, common_exceptions.RepositoryError),
        ):
            raise payment

        gateway_payment_id = await self.payment_repository.get_gateway_payment_id(
            payment.uuid
        )
        if isinstance(
            gateway_payment_id,
            (common_exceptions.PaymentNotFoundError, common_exceptions.RepositoryError),
        ):
            raise gateway_payment_id

        applied_to_subscription = (
            await self.payment_repository.payment_applied_to_subscription(payment.uuid)
        )
        if isinstance(
            applied_to_subscription,
            (common_exceptions.PaymentNotFoundError, common_exceptions.RepositoryError),
        ):
            raise applied_to_subscription
        if applied_to_subscription:
            return

        verify = await self.payment_gateway.verify_payment_complete(gateway_payment_id)

        if isinstance(verify, common_exceptions.PaymentNotComplete) or isinstance(
            verify, common_exceptions.PaymentNotExistsError
        ):
            raise verify

        ensure_res = subscription.ensure_extend()

        if ensure_res:
            raise exceptions.CantExtendSubscription(ensure_res)

        update_data: dict[str, Any] = {"status": entities.SubscriptionStatus.ACTIVE}

        if payment.complete_date is not None:
            update_data["end_date"] = await self.clock.now_date() + timedelta(30)
        else:
            raise exceptions.CantExtendSubscription(
                "Платёж не завершён, невозможно продлить подписку."
            )

        update_res = await self.subscription_repository.update(
            subscription_uuid=subscription.uuid, data=update_data
        )

        if isinstance(
            update_res,
            (
                common_exceptions.SubscriptionNotFoundError,
                common_exceptions.RepositoryError,
            ),
        ):
            raise update_res

        update_payment_res = await self.payment_repository.update(
            payment_uuid=payment.uuid, data={"applied_to_subscription": True}
        )
        if isinstance(
            update_payment_res,
            (common_exceptions.PaymentNotFoundError, common_exceptions.RepositoryError),
        ):
            raise update_payment_res

        await self.session.commit()
        return


class ActivateSubscriptionInteractor:
    def __init__(
        self,
        subscription_repository: common_interfaces.SubscriptionRepository,
        project_repository: common_interfaces.ProjectRepository,
        clock: common_interfaces.Clock,
        session: common_interfaces.DBSession,
        payment_repository: common_interfaces.PaymentRepository,
        payment_gateway: common_interfaces.PaymentGateway,
    ):
        self.subscription_repository = subscription_repository
        self.project_repository = project_repository
        self.clock = clock
        self.session = session
        self.payment_repository = payment_repository
        self.payment_gateway = payment_gateway

    async def execute(self, data: dto.ActivateSubscriptionInDTO) -> None:
        """Активирует подписку по завершённому платежу.

        Args:
            data: Структура ActivateSubscriptionInDTO.
                - project_uuid: UUID
                - payment_uuid: UUID

        Returns:
            None: Подписка успешно активирована.

        Raises:
            common_exceptions.ProjectNotFoundError: Проект не найден.
            common_exceptions.SubscriptionNotFoundError: Подписка не найдена.
            common_exceptions.PaymentNotFoundError: Платёж не найден.
            common_exceptions.PaymentNotComplete: Платёж не завершён.
            common_exceptions.PaymentNotExistsError: Платёж отсутствует в платёжном шлюзе.
            exceptions.CantActivateSubscription: Активация подписки невозможна.
            common_exceptions.RepositoryError: Ошибка репозитория.
        """

        project = await self.project_repository.get_by_uuid(data.project_uuid)
        if isinstance(
            project,
            (common_exceptions.ProjectNotFoundError, common_exceptions.RepositoryError),
        ):
            raise project

        subscription = await self.subscription_repository.get_by_project_uuid(
            data.project_uuid, lock_record=True
        )
        if isinstance(
            subscription,
            (
                common_exceptions.SubscriptionNotFoundError,
                common_exceptions.ProjectNotFoundError,
                common_exceptions.RepositoryError,
            ),
        ):
            raise subscription

        payment = await self.payment_repository.get_by_uuid(data.payment_uuid)
        if isinstance(
            payment,
            (common_exceptions.PaymentNotFoundError, common_exceptions.RepositoryError),
        ):
            raise payment

        gateway_payment_id = await self.payment_repository.get_gateway_payment_id(
            payment.uuid
        )
        if isinstance(
            gateway_payment_id,
            (common_exceptions.PaymentNotFoundError, common_exceptions.RepositoryError),
        ):
            raise gateway_payment_id

        applied_to_subscription = (
            await self.payment_repository.payment_applied_to_subscription(payment.uuid)
        )
        if isinstance(
            applied_to_subscription,
            (common_exceptions.PaymentNotFoundError, common_exceptions.RepositoryError),
        ):
            raise applied_to_subscription
        if applied_to_subscription:
            return

        verify = await self.payment_gateway.verify_payment_complete(gateway_payment_id)
        if isinstance(verify, common_exceptions.PaymentNotComplete) or isinstance(
            verify, common_exceptions.PaymentNotExistsError
        ):
            raise verify

        ensure_res = subscription.ensure_activate()

        if ensure_res:
            raise exceptions.CantActivateSubscription(ensure_res)

        update_res = await self.subscription_repository.update(
            subscription_uuid=subscription.uuid,
            data={
                "status": entities.SubscriptionStatus.ACTIVE,
                "start_date": await self.clock.now_date(),
                "end_date": await self.clock.now_date() + timedelta(30),
            },
        )

        if isinstance(
            update_res,
            (
                common_exceptions.SubscriptionNotFoundError,
                common_exceptions.RepositoryError,
            ),
        ):
            raise update_res

        update_payment_res = await self.payment_repository.update(
            payment_uuid=payment.uuid, data={"applied_to_subscription": True}
        )
        if isinstance(
            update_payment_res,
            (common_exceptions.PaymentNotFoundError, common_exceptions.RepositoryError),
        ):
            raise update_payment_res

        await self.session.commit()
        return


class CreatePaymentInteractor:
    def __init__(
        self,
        subscription_repository: common_interfaces.SubscriptionRepository,
        payment_repository: common_interfaces.PaymentRepository,
        user_repository: common_interfaces.UserRepository,
        project_repository: common_interfaces.ProjectRepository,
        context: common_interfaces.Context,
        clock: common_interfaces.Clock,
        authorization_policy: interfaces.SubscriptionAuthorizationPolicy,
        payment_gateway: common_interfaces.PaymentGateway,
        session: common_interfaces.DBSession,
    ):
        self.subscription_repository = subscription_repository
        self.user_repository = user_repository
        self.context = context
        self.clock = clock
        self.authorization_policy = authorization_policy
        self.project_repository = project_repository
        self.payment_repository = payment_repository
        self.payment_gateway = payment_gateway
        self.session = session

    async def execute(self, data: dto.CreatePaymentInDTO) -> dto.CreatePaymentOutDTO:
        """Создаёт платёж для подписки.

        Args:
            data: Структура CreatePaymentInDTO.
                - uuid: UUID
                - project_uuid: UUID
                - amount: float
                - currency: str

        Returns:
            dto.CreatePaymentOutDTO: Структура результата.
                - process_payment_link: str

        Raises:
            common_exceptions.InvalidTokenError: Токен пользователя невалиден.
            common_exceptions.UserNotFoundError: Пользователь не найден.
            common_exceptions.ProjectNotFoundError: Проект не найден.
            exceptions.SubscriptionAuthorizationError: Недостаточно прав для создания платежа.
            common_exceptions.SubscriptionNotFoundError: Подписка не найдена.
            exceptions.CantCreatePayment: Платёж не может быть создан по доменным ограничениям.
            common_exceptions.PaymentFailedError: Платёжный шлюз вернул ошибку создания платежа.
            common_exceptions.PaymentNotFoundError: Платёж не найден при обновлении данных.
            common_exceptions.RepositoryError: Ошибка репозитория.
        """
        actor_uuid = self.context.get_current_user_uuid()
        if isinstance(actor_uuid, common_exceptions.InvalidTokenError):
            raise actor_uuid

        actor = await self.user_repository.get_by_uuid(actor_uuid)
        if isinstance(
            actor,
            (common_exceptions.UserNotFoundError, common_exceptions.RepositoryError),
        ):
            raise actor

        project = await self.project_repository.get_by_uuid(data.project_uuid)
        if isinstance(
            project,
            (common_exceptions.ProjectNotFoundError, common_exceptions.RepositoryError),
        ):
            raise project

        authorization_error = self.authorization_policy.decide_create_payment(
            actor=actor,
            project=project,
        )
        if authorization_error is not None:
            raise authorization_error

        subscription = await self.subscription_repository.get_by_project_uuid(
            data.project_uuid
        )
        if isinstance(
            subscription,
            (
                common_exceptions.SubscriptionNotFoundError,
                common_exceptions.ProjectNotFoundError,
                common_exceptions.RepositoryError,
            ),
        ):
            raise subscription

        payment = entities.Payment(
            uuid=uuid4(),
            subscription=subscription,
            amount=entities.value_objects.MoneyAmount(
                amount=data.amount,
                currency=entities.value_objects.CurrencyEnum(data.currency),
            ),
            created_at=await self.clock.now_date(),
        )

        ensure_err = payment.ensure_create()
        if ensure_err:
            raise exceptions.CantCreatePayment(ensure_err)

        payment = await self.payment_repository.create(payment)

        if isinstance(
            payment,
            (
                common_exceptions.SubscriptionNotFoundError,
                common_exceptions.RepositoryError,
            ),
        ):
            raise payment

        gateway_payment: (
            tuple[str, UUID] | common_exceptions.PaymentFailedError
        ) = await self.payment_gateway.create_payment(
            actor=actor, project=project, amount=data.amount, payment=payment
        )

        if isinstance(gateway_payment, common_exceptions.PaymentFailedError):
            raise gateway_payment

        update_gateway_id_result = await self.payment_repository.update(
            payment_uuid=payment.uuid,
            data={"gateway_payment_id": str(gateway_payment[1])},
        )
        if isinstance(
            update_gateway_id_result,
            (common_exceptions.PaymentNotFoundError, common_exceptions.RepositoryError),
        ):
            raise update_gateway_id_result

        await self.session.commit()

        return dto.CreatePaymentOutDTO(gateway_payment[0])


class CompletePaymentInteractor:
    def __init__(
        self,
        payment_repository: common_interfaces.PaymentRepository,
        user_repository: common_interfaces.UserRepository,
        project_repository: common_interfaces.ProjectRepository,
        clock: common_interfaces.Clock,
        payment_gateway: common_interfaces.PaymentGateway,
        session: common_interfaces.DBSession,
    ):
        self.user_repository = user_repository
        self.clock = clock
        self.project_repository = project_repository
        self.payment_repository = payment_repository
        self.payment_gateway = payment_gateway
        self.session = session

    async def execute(self, data: dto.CompletePaymentInDTO) -> None:
        """Помечает платёж завершённым.

        Args:
            data: Структура CompletePaymentInDTO.
                - payment_uuid: UUID

        Returns:
            None: Платёж успешно завершён.

        Raises:
            common_exceptions.PaymentNotFoundError: Платёж не найден.
            common_exceptions.PaymentNotComplete: Платёж не подтверждён.
            common_exceptions.PaymentNotExistsError: Платёж отсутствует в платёжном шлюзе.
            exceptions.CantCompletePayment: Платёж не может быть завершён по доменным ограничениям.
            common_exceptions.PaymentRefundFailedError: Не удалось выполнить возврат платежа.
            common_exceptions.RepositoryError: Ошибка репозитория.
        """

        gateway_payment_id = await self.payment_repository.get_gateway_payment_id(
            data.payment_uuid
        )
        if isinstance(
            gateway_payment_id,
            (common_exceptions.PaymentNotFoundError, common_exceptions.RepositoryError),
        ):
            raise gateway_payment_id

        is_verified = await self.payment_gateway.verify_payment_complete(
            gateway_payment_id
        )
        if isinstance(is_verified, common_exceptions.PaymentNotComplete) or isinstance(
            is_verified, common_exceptions.PaymentNotExistsError
        ):
            raise is_verified

        if not is_verified:
            raise exceptions.CantCompletePayment(
                "Платёж не подтверждён платёжной системой."
            )

        payment = await self.payment_repository.get_by_uuid(
            data.payment_uuid, lock_record=True
        )
        if isinstance(
            payment,
            (common_exceptions.PaymentNotFoundError, common_exceptions.RepositoryError),
        ):
            raise payment

        complete_err = payment.ensure_complete()

        if complete_err:
            refund_result = await self.payment_gateway.refund_payment(
                payment, gateway_payment_id
            )
            if isinstance(
                refund_result,
                (
                    common_exceptions.PaymentRefundFailedError,
                    common_exceptions.PaymentNotExistsError,
                ),
            ):
                raise refund_result
            raise exceptions.CantCompletePayment(complete_err)

        payment_error = await self.payment_repository.update(
            payment_uuid=payment.uuid, data={"status": entities.PaymentStatus.COMPLETED}
        )

        if isinstance(
            payment_error,
            (common_exceptions.PaymentNotFoundError, common_exceptions.RepositoryError),
        ):
            raise payment_error

        await self.session.commit()
        return


class CompletePaymentAndUpdateSubscriptionInteractor:
    def __init__(
        self,
        subscription_repository: common_interfaces.SubscriptionRepository,
        payment_repository: common_interfaces.PaymentRepository,
        user_repository: common_interfaces.UserRepository,
        project_repository: common_interfaces.ProjectRepository,
        clock: common_interfaces.Clock,
        payment_gateway: common_interfaces.PaymentGateway,
        session: common_interfaces.DBSession,
    ):
        self.subscription_repository = subscription_repository
        self.user_repository = user_repository
        self.clock = clock
        self.project_repository = project_repository
        self.payment_repository = payment_repository
        self.payment_gateway = payment_gateway
        self.session = session

    async def execute(
        self, data: dto.CompletePaymentAndUpdateSubscriptionInDTO
    ) -> None:
        """Завершает платёж и приводит подписку в актуальное состояние.

        Args:
            data: Структура CompletePaymentAndUpdateSubscriptionInDTO.
                - project_uuid: UUID
                - payment_uuid: UUID

        Returns:
            None: Платёж завершён и подписка обновлена.

        Raises:
            common_exceptions.PaymentNotFoundError: Платёж не найден.
            common_exceptions.PaymentNotComplete: Платёж не подтверждён.
            common_exceptions.PaymentNotExistsError: Платёж отсутствует в платёжном шлюзе.
            common_exceptions.PaymentRefundFailedError: Не удалось выполнить возврат платежа.
            exceptions.CantCompletePayment: Платёж не может быть завершён.
            common_exceptions.ProjectNotFoundError: Проект не найден.
            common_exceptions.SubscriptionNotFoundError: Подписка не найдена.
            exceptions.CantExtendSubscription: Подписку нельзя продлить.
            exceptions.CantActivateSubscription: Подписку нельзя активировать.
            common_exceptions.RepositoryError: Ошибка репозитория.
        """

        await CompletePaymentInteractor(
            payment_repository=self.payment_repository,
            user_repository=self.user_repository,
            project_repository=self.project_repository,
            clock=self.clock,
            payment_gateway=self.payment_gateway,
            session=self.session,
        ).execute(dto.CompletePaymentInDTO(payment_uuid=data.payment_uuid))

        subscription = await self.subscription_repository.get_by_project_uuid(
            data.project_uuid
        )
        if isinstance(
            subscription,
            (
                common_exceptions.SubscriptionNotFoundError,
                common_exceptions.ProjectNotFoundError,
                common_exceptions.RepositoryError,
            ),
        ):
            raise subscription

        extend_ensure_res = subscription.ensure_extend()

        if extend_ensure_res:
            raise exceptions.CantExtendSubscription(extend_ensure_res)
        await ExtendSubscriptionInteractor(
            subscription_repository=self.subscription_repository,
            project_repository=self.project_repository,
            payment_repository=self.payment_repository,
            payment_gateway=self.payment_gateway,
            clock=self.clock,
            session=self.session,
        ).execute(
            dto.ExtendSubscriptionInDTO(
                project_uuid=data.project_uuid, payment_uuid=data.payment_uuid
            )
        )

        ensure_activate_res = subscription.ensure_activate()

        if ensure_activate_res:
            raise exceptions.CantActivateSubscription(ensure_activate_res)
        await ActivateSubscriptionInteractor(
            subscription_repository=self.subscription_repository,
            project_repository=self.project_repository,
            clock=self.clock,
            session=self.session,
            payment_repository=self.payment_repository,
            payment_gateway=self.payment_gateway,
        ).execute(
            dto.ActivateSubscriptionInDTO(
                project_uuid=data.project_uuid, payment_uuid=data.payment_uuid
            )
        )

        return
